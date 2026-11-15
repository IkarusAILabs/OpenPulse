"""Poetry writes format metadata in a table, after its package entries."""

import pytest

from core.lockfile_reader import load_poetry_lock_doc, lockfile_digests, read_lockfile


@pytest.fixture
def poetry_lock(tmp_path):
    path = tmp_path / "dependencies.txt"  # Detection must not depend on the filename.
    path.write_text(
        '[[package]]\nname = "django"\nversion = "4.2"\n'
        'files = [{file = "django.whl", hash = "sha256:' + "a" * 64 + '"}]\n\n'
        '[metadata]\nlock-version = "2.1"\npython-versions = ">=3.11"\n'
        'content-hash = "synthetic"\n'
    )
    return path


def test_poetry_metadata_table_is_recognized(poetry_lock):
    deps, skipped, fmt = read_lockfile(str(poetry_lock))
    assert fmt == "poetry"
    assert deps == [{"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}]
    assert skipped == []


def test_poetry_metadata_table_enables_digest_loading(poetry_lock):
    assert lockfile_digests(str(poetry_lock)) == {("PyPI", "django", "4.2"): {"sha256": ["a" * 64]}}


def test_empty_poetry_lock_with_metadata_is_valid(tmp_path):
    path = tmp_path / "poetry.lock"
    path.write_text('[metadata]\nlock-version = "2.1"\n')
    assert read_lockfile(str(path)) == ([], [], "poetry")


@pytest.mark.parametrize("metadata", [None, [], "2.1", {"python-versions": ">=3.11"}])
def test_non_poetry_metadata_does_not_identify_a_lockfile(metadata):
    with pytest.raises(ValueError, match="lock-version"):
        load_poetry_lock_doc({"metadata": metadata, "package": []})
