"""M5: webhook delivery is pinned to the addresses the SSRF check validated.

Offline: `socket.getaddrinfo` is replaced by a scripted resolver and
`socket.create_connection` by a fake that records where the client tried
to connect and serves a canned HTTP response over a loopback TCP pair.
A hostname handed to the fake is resolved through the scripted resolver,
just as the real `create_connection` would, so an unpinned client is
caught taking the second (rebound) answer.
"""

from __future__ import annotations

import ipaddress
import socket
import ssl
import threading

import pytest

PUBLIC = "93.184.216.34"
PUBLIC_2 = "93.184.216.35"
URL_PATH = "/hook/T000/B000/secret-token"


def _tcp_pair() -> tuple[socket.socket, socket.socket]:
    """A connected loopback TCP pair.

    Not `socket.socketpair()`: on Linux that is AF_UNIX, and httpcore sets
    TCP_NODELAY on every socket it dials, which an AF_UNIX socket rejects
    (EOPNOTSUPP). Windows emulates socketpair over TCP, so only Linux failed.
    `socket.create_connection` is patched here, so connect directly.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(listener.getsockname())
        server, _ = listener.accept()
    return client, server


class _Net:
    def __init__(self, monkeypatch, answers):
        self.answers = list(answers)
        self.lookups: list[str] = []
        self.dialed: list[tuple[str, int]] = []  # what the client asked for
        self.reached: list[str] = []  # the IP that connection would hit
        self.requests: list[bytes] = []
        self.refuse: set[str] = set()
        monkeypatch.setattr(socket, "getaddrinfo", self.getaddrinfo)
        monkeypatch.setattr(socket, "create_connection", self.create_connection)

    def getaddrinfo(self, host, port, *args, **kwargs):
        self.lookups.append(host)
        ip = self.answers[min(len(self.lookups), len(self.answers)) - 1]
        family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        return [(family, socket.SOCK_STREAM, 6, "", (ip, port or 0))]

    def create_connection(self, address, timeout=None, source_address=None, **kwargs):
        host, port = address
        self.dialed.append((host, port))
        try:
            ip = str(ipaddress.ip_address(host))
        except ValueError:
            ip = self.getaddrinfo(host, port)[0][4][0]
        self.reached.append(ip)
        if ip in self.refuse:
            raise ConnectionRefusedError("refused")
        client, server = _tcp_pair()
        threading.Thread(target=self._serve, args=(server,), daemon=True).start()
        return client

    def _serve(self, sock):
        with sock:
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = sock.recv(65536)
                if not chunk:
                    return
                data += chunk
            head, _, body = data.partition(b"\r\n\r\n")
            length = 0
            for line in head.split(b"\r\n")[1:]:
                name, _, value = line.partition(b":")
                if name.strip().lower() == b"content-length":
                    length = int(value)
            while len(body) < length:
                body += sock.recv(65536)
            self.requests.append(head + b"\r\n\r\n" + body)
            sock.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok")


def _http_policy():
    from core.notify import WebhookPolicy

    return WebhookPolicy(allow_http=True)


@pytest.mark.parametrize("rebound", ["127.0.0.1", "169.254.169.254"])
def test_rebinding_resolver_never_reaches_the_private_address(monkeypatch, rebound):
    from core.notify import post_digest

    net = _Net(monkeypatch, [PUBLIC, rebound])
    result = post_digest(f"http://hooks.example{URL_PATH}", "md", policy=_http_policy())

    assert rebound not in net.reached
    assert net.reached == [PUBLIC]
    assert net.lookups == ["hooks.example"]  # resolved once, never again
    assert result["ok"] is True


def test_rebinding_resolver_never_reaches_the_private_address_over_https(monkeypatch):
    from core.notify import post_digest

    net = _Net(monkeypatch, [PUBLIC, "127.0.0.1"])

    def stop_tls(self, sock, server_hostname=None, **kwargs):
        raise ssl.SSLError("offline test stops at the handshake")

    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", stop_tls)
    result = post_digest(f"https://hooks.example{URL_PATH}", "md")

    assert net.reached == [PUBLIC]
    assert result["ok"] is False
    assert URL_PATH not in (result["error"] or "")


@pytest.mark.parametrize(
    "address, embedded, form",
    [
        ("::ffff:127.0.0.1", "127.0.0.1", "IPv4-mapped"),
        ("::ffff:169.254.169.254", "169.254.169.254", "IPv4-mapped"),
        ("::ffff:10.0.0.1", "10.0.0.1", "IPv4-mapped"),
        ("2002:7f00:1::", "127.0.0.1", "6to4"),
        ("2002:a9fe:a9fe::1", "169.254.169.254", "6to4"),
        ("64:ff9b::7f00:1", "127.0.0.1", "NAT64"),
        ("64:ff9b::a9fe:a9fe", "169.254.169.254", "NAT64"),
        ("64:ff9b:1:7f00:0:100::", "127.0.0.1", "NAT64"),  # RFC 6052 /48 layout
        ("64:ff9b:1::a9fe:a9fe", "169.254.169.254", "NAT64"),  # /96 layout in local-use
    ],
)
def test_wrapped_ipv4_is_unwrapped_and_blocked(address, embedded, form):
    from core.notify import post_digest, validate_webhook_url

    ok, reason = validate_webhook_url("https://hooks.example/x", resolver=lambda host: [address])
    assert ok is False
    assert embedded in reason and form in reason

    ok, reason = validate_webhook_url(f"https://[{address}]/x")
    assert ok is False
    assert embedded in reason and form in reason

    result = post_digest("https://hooks.example/x", "md", resolver=lambda host: [address])
    assert result["ok"] is False and embedded in result["error"]


def test_any_blocked_address_refuses_and_says_why():
    from core.notify import validate_webhook_url

    ok, reason = validate_webhook_url(
        "https://hooks.example/x", resolver=lambda host: [PUBLIC, "64:ff9b::7f00:1"]
    )
    assert ok is False
    assert "127.0.0.1" in reason and "NAT64" in reason


def test_sni_and_certificate_check_stay_on_the_hostname(monkeypatch):
    from core.notify import post_digest

    net = _Net(monkeypatch, [PUBLIC])
    handshakes = []

    def record_tls(self, sock, server_hostname=None, **kwargs):
        handshakes.append((server_hostname, self.check_hostname, self.verify_mode))
        raise ssl.SSLError("offline test stops at the handshake")

    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", record_tls)
    result = post_digest(f"https://hooks.example{URL_PATH}", "md")

    assert net.dialed == [(PUBLIC, 443)]  # the IP, not the name
    assert handshakes == [("hooks.example", True, ssl.CERT_REQUIRED)]
    assert result["ok"] is False


def test_valid_public_address_still_delivers_with_original_host_header(monkeypatch):
    from core.notify import post_digest

    net = _Net(monkeypatch, [PUBLIC])
    result = post_digest(f"http://hooks.example:8080{URL_PATH}", "hello", policy=_http_policy())

    assert result == {"ok": True, "status_code": 200, "error": None}
    assert net.dialed == [(PUBLIC, 8080)]
    assert net.lookups == ["hooks.example"]
    head = net.requests[0].split(b"\r\n\r\n")[0].lower()
    assert head.startswith(f"post {URL_PATH} http/1.1".lower().encode())
    assert b"\r\nhost: hooks.example:8080" in head
    assert net.requests[0].endswith(b'{"text":"hello"}')


def test_falls_back_only_to_other_validated_addresses(monkeypatch):
    from core.notify import post_digest

    net = _Net(monkeypatch, [PUBLIC])
    net.refuse.add(PUBLIC)
    result = post_digest(
        f"http://hooks.example{URL_PATH}",
        "md",
        policy=_http_policy(),
        resolver=lambda host: [PUBLIC, PUBLIC_2],
    )

    assert net.dialed == [(PUBLIC, 80), (PUBLIC_2, 80)]
    assert result["ok"] is True


def test_pinned_backend_refuses_any_other_host():
    import httpcore

    from core.notify import _PinnedBackend

    class Inner(httpcore.NetworkBackend):
        def connect_tcp(self, *args, **kwargs):  # pragma: no cover - must not run
            raise AssertionError("dialed")

    backend = _PinnedBackend("hooks.example", [PUBLIC], inner=Inner())
    with pytest.raises(httpcore.ConnectError):
        backend.connect_tcp("internal.example", 443)
