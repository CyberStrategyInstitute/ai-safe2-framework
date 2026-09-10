"""Bounded inventory for immutable, local scanner inputs; no silent exclusions."""
from __future__ import annotations

import os
import stat
from pathlib import Path

from safe2.challenge.io import safe_path


def inventory(root: Path, *, max_entries: int) -> list[Path]:
    if max_entries < 1:
        raise ValueError("entry limit must be positive")
    root = safe_path(root)
    pending = [root]
    files: list[Path] = []
    count = 0
    while pending:
        current = safe_path(pending.pop())
        info = current.lstat()
        if stat.S_ISREG(info.st_mode):
            files.append(current)
        elif stat.S_ISDIR(info.st_mode):
            with os.scandir(current) as entries:
                for entry in entries:
                    count += 1
                    if count > max_entries:
                        raise ValueError("entry-count limit exceeded; coverage is incomplete")
                    pending.append(Path(entry.path))
        else:
            raise ValueError("special files are not allowed")
    return sorted(files)
