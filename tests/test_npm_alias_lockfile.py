"""Registry aliases must be checked under their actual npm package names."""

import json

import pytest

from core.lockfile_reader import load_package_lock_doc, lockfile_digests, read_lockfile


@pytest.mark.parametrize("lock_version", [2, 3])
@pytest.mark.parametrize(
    "path,name",
    [
        ("node_modules/number-alias", "is-number"),
        ("node_modules/parent/node_modules/alias", "@scope/actual"),
        ("node_modules/@local/alias", "is-number"),
    ],
)
def test_alias_dependency_and_digest_use_registry_identity(tmp_path, lock_version, path, name):
    # npm install --package-lock-only --ignore-scripts number-alias@npm:is-number@7.0.0
    # writes the registry name into the aliased packages entry's `name` field.
    doc = {
        "lockfileVersion": lock_version,
        "packages": {path: {"name": name, "version": "7.0.0", "integrity": "sha512-synthetic"}},
    }
    lock = tmp_path / "package-lock.json"
    lock.write_text(json.dumps(doc))
    deps, skipped, fmt = read_lockfile(str(lock))
    assert fmt == "npm"
    assert deps == [{"kind": "package", "package": name, "ecosystem": "npm", "version": "7.0.0"}]
    assert skipped == []
    assert lockfile_digests(str(lock)) == {
        ("npm", name, "7.0.0"): {"integrity": ["sha512-synthetic"]}
    }


def test_regular_package_without_explicit_name_keeps_path_identity(tmp_path):
    doc = {
        "lockfileVersion": 3,
        "packages": {
            "node_modules/@scope/regular": {"version": "1.0.0", "integrity": "sha512-synthetic"}
        },
    }
    lock = tmp_path / "package-lock.json"
    lock.write_text(json.dumps(doc))
    deps, skipped = load_package_lock_doc(doc)
    assert deps[0]["package"] == "@scope/regular"
    assert skipped == []
    assert ("npm", "@scope/regular", "1.0.0") in lockfile_digests(str(lock))


def test_workspace_link_is_still_skipped_when_it_has_a_name():
    deps, skipped = load_package_lock_doc(
        {
            "lockfileVersion": 3,
            "packages": {
                "node_modules/alias": {"name": "workspace", "link": True, "version": "1.0.0"}
            },
        }
    )
    assert deps == []
    assert len(skipped) == 1
    assert "workspace link" in skipped[0]
