"""write_new_atomic must distinguish 'never published' from 'published, staging link left behind'."""

from __future__ import annotations

from pathlib import Path

import pytest

from safe2.secure_io import PublishedCleanupError, write_new_atomic


def test_a_failed_staging_cleanup_after_publication_is_reported_as_published(tmp_path: Path, monkeypatch) -> None:
    real = Path.unlink

    def unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name.endswith(".tmp"):
            raise PermissionError("locked")
        real(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)
    target = tmp_path / "out.json"
    with pytest.raises(PublishedCleanupError) as caught:
        write_new_atomic(target, b"payload")
    assert isinstance(caught.value, OSError)
    assert caught.value.path == target and caught.value.temporary.name.endswith(".tmp")
    assert target.read_bytes() == b"payload"


def test_an_existing_target_is_not_reported_as_published(tmp_path: Path) -> None:
    target = tmp_path / "out.json"
    target.write_bytes(b"old")
    with pytest.raises(FileExistsError):
        write_new_atomic(target, b"new")
    assert target.read_bytes() == b"old"
    assert [p.name for p in tmp_path.iterdir()] == ["out.json"]
