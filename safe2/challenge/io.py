"""Bounded, strict artifact I/O with explicit no-overwrite behavior."""

from __future__ import annotations

import json
import os
import secrets
import stat
import sys
from pathlib import Path
from typing import Any

MAX_BYTES = 20_000_000


def _link_open_descriptor(descriptor: int, target: Path, temporary: Path) -> None:
    """Publish an already-synced inode without replacing the destination."""
    if sys.platform.startswith("linux"):
        # Python's os.link may select link(2), which treats /proc/self/fd/N as
        # a procfs inode and fails EXDEV. linkat(2) with AT_SYMLINK_FOLLOW is
        # the kernel-documented way to bind the destination to the open file.
        import ctypes

        source = f"/proc/self/fd/{descriptor}".encode()
        libc = ctypes.CDLL(None, use_errno=True)
        linkat = libc.linkat
        linkat.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        linkat.restype = ctypes.c_int
        if linkat(-100, source, -100, os.fsencode(target), 0x400) != 0:  # AT_SYMLINK_FOLLOW
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(target))
        return
    # Windows prevents replacement of this CRT-opened file. Other supported
    # platforms retain the descriptor and verify the published inode below.
    os.link(temporary, target, follow_symlinks=False)


def safe_path(path: str | Path) -> Path:
    """Reject links/reparse points in every existing component, including parents."""
    target = Path(os.path.abspath(path))
    if os.name == "nt" and (
        str(target).startswith("\\\\")
        or (os.path.isreserved(target) if hasattr(os.path, "isreserved") else target.is_reserved())
        or any(":" in part for part in target.parts[1:])
    ):
        raise ValueError("Device, network-share, and alternate-stream paths are not allowed")
    for component in (*reversed(target.parents), target):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or (getattr(info, "st_file_attributes", 0) or 0) & 0x400:
            raise ValueError("Symbolic links and reparse paths are not allowed")
    return target


def read_bytes(path: str | Path, *, limit: int = MAX_BYTES) -> bytes:
    target = safe_path(path)
    before = target.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError("Input must be a regular file within the size limit")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    # A replaced leaf must not turn a bounded read into a blocking FIFO open.
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(target, flags)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if (before.st_dev, before.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError("Input changed identity while being opened")
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("Input must be a regular file within the size limit")
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Input size limit exceeded")
    return data


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON keys are not allowed")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("Non-finite JSON numbers are not allowed")


def parse_json(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_BYTES:
        raise ValueError("Input size limit exceeded")
    try:
        value = json.loads(data, object_pairs_hook=_pairs, parse_constant=_invalid_constant)
        # Also catches overflowing exponents such as 1e999.
        json.dumps(value, allow_nan=False)
    except (UnicodeError, json.JSONDecodeError, RecursionError, OverflowError) as exc:
        raise ValueError("Invalid or excessively nested JSON artifact") from exc
    if not isinstance(value, dict):
        raise ValueError("Artifact must be a JSON object")  # noqa: TRY004 -- public parse contract
    return value


def read_json(path: str | Path) -> dict[str, Any]:
    return parse_json(read_bytes(path))


def write_text(path: str | Path, value: str) -> None:
    encoded = value.encode("utf-8")
    if len(encoded) > MAX_BYTES:
        raise ValueError("Output size limit exceeded")
    target = safe_path(path)
    temporary = safe_path(target.parent / f".{target.name}.safe2-{secrets.token_hex(16)}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    identity = None
    try:
        descriptor = os.open(temporary, flags, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            identity = os.fstat(handle.fileno())
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
            _link_open_descriptor(handle.fileno(), target, temporary)
            published = target.lstat()
            current = os.fstat(handle.fileno())
            if (published.st_dev, published.st_ino) != (current.st_dev, current.st_ino):
                raise OSError("Published output does not match generated file")
    finally:
        if identity is not None:
            try:
                current = temporary.lstat()
                if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                    temporary.unlink()
            except FileNotFoundError:
                pass


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
