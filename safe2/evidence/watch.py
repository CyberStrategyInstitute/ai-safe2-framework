"""Explicit, local polling runner for agent-input change evidence."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any

from safe2.adapters.conformance import AdapterError, load_json_regular
from safe2.challenge.io import safe_path, write_text
from safe2.evidence.change_monitor import monitor

MAX_STATE_BYTES = 5_000_000


def _regular_or_missing(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ValueError(f"{label} must be a regular, non-symlink file")


def load_state(path: Path) -> dict[str, Any] | None:
    path = safe_path(path)
    _regular_or_missing(path, "Watch state")
    if not path.exists():
        return None
    try:
        return load_json_regular(path, max_bytes=MAX_STATE_BYTES)
    except AdapterError as exc:
        raise ValueError("Watch state must be bounded, valid JSON") from exc


def _serialized(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _write_new(path: Path, body: bytes) -> None:
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path = safe_path(path)
    if path.exists():
        raise ValueError(f"Evidence output already exists: {path.name}")
    write_text(path, body.decode("utf-8"))


def _replace_state(path: Path, body: bytes) -> None:
    path = safe_path(path)
    _regular_or_missing(path, "Watch state")
    path.parent.mkdir(parents=True, exist_ok=True)
    path = safe_path(path)
    temporary = safe_path(path.with_name(f".{path.name}.{secrets.token_hex(16)}.tmp"))
    _regular_or_missing(temporary, "Temporary watch state")
    if temporary.exists():
        raise ValueError("Temporary watch-state path already exists")
    try:
        with temporary.open("xb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def collect_once(
    root: Path,
    state_path: Path,
    evidence_dir: Path,
    *,
    max_files: int = 10_000,
    max_file_bytes: int = 1_000_000,
) -> tuple[dict[str, Any], Path]:
    """Collect one bounded report, preserve it immutably, then advance state."""
    baseline = load_state(state_path)
    result = monitor(
        root,
        baseline,
        max_files=max_files,
        max_file_bytes=max_file_bytes,
    )
    body = _serialized(result)
    digest = hashlib.sha256(body).hexdigest()
    stamp = result["created_at"].replace(":", "").replace("+", "_")
    report_path = evidence_dir / f"change-{stamp}-{digest[:12]}.json"
    if report_path.resolve(strict=False) == state_path.resolve(strict=False):
        raise ValueError("Evidence report and watch state must be distinct")
    _write_new(report_path, body)
    _replace_state(state_path, body)
    return result, report_path
