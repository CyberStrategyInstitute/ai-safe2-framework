"""Append-only hash-chained decision event ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def append_event(path: Path, event: dict[str, Any]) -> str:
    if path.is_symlink():
        raise ValueError("audit ledger must not be a symbolic link")
    previous = "0" * 64
    if path.exists():
        if path.stat().st_size > 50_000_000:
            raise ValueError("audit ledger exceeds 50 MB")
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            last = json.loads(lines[-1])
            previous = str(last["event_sha256"])
    body = {"previous_event_sha256": previous, "event": event}
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    record = {**body, "event_sha256": digest}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return digest
