"""Tests for the repository-URL rule (PROTOCOL.md §4).

python -m pytest papers/prevalence/test_collect.py
"""

import pytest
from collect import github_repo_from_url

ACCEPTED = [
    ("https://github.com/chalk/supports-color", "chalk/supports-color"),
    ("https://github.com/chalk/supports-color.git", "chalk/supports-color"),
    ("git+https://github.com/babel/babel.git", "babel/babel"),
    ("git://github.com/isaacs/rimraf.git", "isaacs/rimraf"),
    ("git+ssh://git@github.com/org/repo.git", "org/repo"),
    ("git@github.com:org/repo.git", "org/repo"),
    ("https://www.github.com/org/repo/", "org/repo"),
    ("https://github.com/pytest-dev/pytest-cov/issues", "pytest-dev/pytest-cov"),
    ("https://github.com/tensorflow/tensorflow/tags", "tensorflow/tensorflow"),
    ("github.com/stretchr/testify", "stretchr/testify"),
    ("HTTPS://GitHub.com/Org/Repo", "Org/Repo"),
]

REJECTED = [
    "https://mygithub.com/org/repo",
    "https://example.org/github.com/org/repo",
    "https://github.com.evil.example/org/repo",
    "https://gitlab.com/org/repo",
    "https://github.com/org",
    "https://pycodestyle.pycqa.org/",
    "github:org/repo",  # npm shorthand is only accepted for npm
    "org/repo",
    "",
    None,
]


@pytest.mark.parametrize(("url", "expected"), ACCEPTED)
def test_accepts_github_references(url, expected):
    assert github_repo_from_url(url) == expected


@pytest.mark.parametrize("url", REJECTED)
def test_rejects_everything_else(url):
    assert github_repo_from_url(url) is None


@pytest.mark.parametrize(
    ("url", "expected"),
    [("github:org/repo", "org/repo"), ("org/repo", "org/repo"), ("gitlab:org/repo", None)],
)
def test_npm_shorthand(url, expected):
    assert github_repo_from_url(url, npm_shorthand=True) == expected


def test_npm_shorthand_does_not_swallow_hosts():
    assert github_repo_from_url("gitlab.com/org/repo", npm_shorthand=True) is None
    assert github_repo_from_url("github.com/org/repo", npm_shorthand=True) == "org/repo"


def test_the_client_refuses_anything_but_https():
    from collect import Http

    client = Http.__new__(Http)  # no log file or token needed to reach the check
    for url in ("file:///etc/passwd", "http://pypi.org/pypi/x/json", "ftp://example.org/x"):
        with pytest.raises(ValueError, match="non-https"):
            client.request(url)
