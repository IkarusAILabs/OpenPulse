#!/usr/bin/env sh
# Reproduce the TR-2026-01 audit result (Appendix B) from a clean clone.
#
#   sh papers/tr-2026-01/reproduce_audit.sh [path-to-OpenPulse-clone]
#
# Runs tests/test_false_clear.py from the pinned commit against the
# audited commit (transplanted, since the file does not exist there) and
# against the pinned commit itself. Expected: 52 failed, 12 passed at
# the audited commit; 64 passed at the pinned commit.
# Needs git, and a Python with the project's requirements.lock installed
# (set PYTHON to choose the interpreter). Runs offline.
set -eu

AUDITED=a461bc99a6edebbdb124e4b9a3c477282aae45a6
PINNED=8a9c3a829ad0da7a8a1e935f677af0eb8810ed0c
REPO=${1:-.}
PYTHON=${PYTHON:-python}
WORK=$(mktemp -d)
trap 'git -C "$REPO" worktree remove --force "$WORK/audited" >/dev/null 2>&1 || true;
      git -C "$REPO" worktree remove --force "$WORK/pinned" >/dev/null 2>&1 || true;
      rm -rf "$WORK"' EXIT

git -C "$REPO" worktree add --detach "$WORK/audited" "$AUDITED" >/dev/null
git -C "$REPO" worktree add --detach "$WORK/pinned" "$PINNED" >/dev/null
git -C "$REPO" show "$PINNED:tests/test_false_clear.py" > "$WORK/audited/tests/test_false_clear.py"

run() {
    echo "== $1 =="
    (cd "$2" && "$PYTHON" -m pytest -p no:cacheprovider -q -rA tests/test_false_clear.py) \
        | grep -E '^(PASSED|FAILED) |passed|failed' || true
}

run "audited commit $AUDITED (expected: 52 failed, 12 passed)" "$WORK/audited"
run "pinned commit $PINNED (expected: 64 passed)" "$WORK/pinned"
