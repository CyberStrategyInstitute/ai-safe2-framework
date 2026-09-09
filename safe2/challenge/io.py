"""Bounded, strict artifact I/O with explicit no-overwrite behavior."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

MAX_BYTES = 20_000_000


def safe_path(path: str | Path) -> Path:
    """Reject links/reparse points in every existing component, including parents."""
    target = Path(os.path.abspath(path))
    if os.name == "nt" and (
        str(target).startswith("\\\\")
        or target.is_reserved()
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
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise ValueError("Input must be a regular file within the size limit")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    # A replaced leaf must not turn a bounded read into a blocking FIFO open.
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(target, flags)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
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
    # Deliberately do not create implicit directory trees.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
