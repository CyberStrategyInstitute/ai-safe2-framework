"""Small fail-closed filesystem primitives shared by security-sensitive CLI paths."""

from __future__ import annotations

import os
import secrets
import stat
from pathlib import Path


def reject_symlink_ancestry(path: Path, *, include_leaf: bool = True) -> None:
    """Reject existing symbolic links anywhere in a path's absolute ancestry."""
    absolute = path.absolute()
    parts = absolute.parents if not include_leaf else (absolute, *absolute.parents)
    for candidate in parts:
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValueError(f"path ancestry is not inspectable: {candidate}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"symbolic-link path components are not allowed: {candidate}")


def read_regular_bounded(path: Path, *, limit: int) -> bytes:
    """Open once without following the leaf symlink, validate, and read at most limit bytes."""
    reject_symlink_ancestry(path.parent)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"input is not a readable regular file: {path}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"input is not a regular file: {path}")
        if info.st_size > limit:
            raise ValueError(f"input exceeds {limit} bytes")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            body = handle.read(limit + 1)
        if len(body) > limit:
            raise ValueError(f"input exceeds {limit} bytes")
        return body
    finally:
        os.close(descriptor)


class PublishedCleanupError(OSError):
    """The file was published at `path`, but its staging hard link could not be removed.

    Callers must treat the output as written: the content is in place and complete. Only the
    leftover `temporary` name remains to be cleaned up.
    """

    def __init__(self, path: Path, temporary: Path, cause: OSError) -> None:
        super().__init__(f"{path} was written, but the staging file {temporary} could not be removed: {cause}")
        self.path = path
        self.temporary = temporary


def write_new_atomic(path: Path, body: bytes, *, mode: int = 0o600) -> None:
    """Durably stage bytes and publish them at a new path without overwriting.

    Raises PublishedCleanupError (an OSError) when publication succeeded and only removing the
    staging link failed, so a caller can tell that apart from a write that never happened.
    """
    reject_symlink_ancestry(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    reject_symlink_ancestry(path.parent)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(16)}.tmp")
    descriptor: int | None = None
    published = False
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.close(descriptor)
        descriptor = None
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise FileExistsError(f"output already exists: {path}") from exc
        published = True
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            if published:
                raise PublishedCleanupError(path, temporary, exc) from exc
            raise
