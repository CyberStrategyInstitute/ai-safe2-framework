"""Operator-requested local process observation. Not a sandbox or remote attestation."""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from safe2.bounded_process import run_bounded
from safe2.challenge.integrity import canonical_bytes
from safe2.challenge.io import safe_path
from safe2.contracts import validate_artifact


def capture_process(
    command: tuple[str, ...], *, cwd: Path, task_id: str, revision: str,
    environment: str, call_id: str, tool: str, timeout: int = 60, max_bytes: int = 1_000_000,
) -> dict[str, Any]:
    """Run only explicitly supplied argv, with closed stdin and a small environment.

    No shell interpolation, provider keys, raw output retention, or automatic signing.
    Descendant containment and filesystem/network isolation require an external sandbox.
    """
    if not command or len(command) > 128 or sum(len(item) for item in command) > 32768:
        raise ValueError("An explicit bounded command is required")
    if not 1 <= timeout <= 3600 or not 1 <= max_bytes <= 10_000_000:
        raise ValueError("Invalid process limits")
    executable = Path(command[0])
    if not executable.is_absolute():
        raise ValueError("Use an explicit absolute executable path, not PATH lookup")
    executable = safe_path(executable)
    if os.name == "nt" and executable.suffix.lower() in {".bat", ".cmd"}:
        raise ValueError("Batch files require explicit shell execution; implicit shell launch rejected")
    directory = safe_path(cwd)
    if not directory.is_dir():
        raise ValueError("Working directory must exist")
    report: dict[str, Any] = {
        "schema_version": "safe2.tool-result.v1", "task_id": task_id,
        "revision": revision, "environment": environment, "call_id": call_id, "tool": tool,
        "source_ref": f"local-process-{uuid.uuid4()}", "outcome": "unknown",
    }
    if validate_artifact("tool-result-v1", report):
        raise ValueError("Invalid task, revision, environment, call, or tool identifier")
    # Not a security boundary: a same-user child may still read credentials from disk.
    allowed = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    child_env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    child_env.update({"PYTHONUTF8": "1", "NO_COLOR": "1"})
    started = time.monotonic()
    exit_code = None
    stdout_hash = stderr_hash = None
    output_complete = False
    try:
        result = run_bounded([str(executable), *command[1:]], cwd=directory, env=child_env,
                             timeout=timeout, max_bytes=max_bytes)
        exit_code = result.returncode
        stdout_hash = hashlib.sha256(result.stdout).hexdigest()
        stderr_hash = hashlib.sha256(result.stderr).hexdigest()
        output_complete = result.output_complete
        if result.exceeded:
            capture_status = "output_limit"
        elif not output_complete:
            capture_status = "drain_incomplete"
        else:
            capture_status = "completed"
            report["outcome"] = "succeeded" if exit_code == 0 else "failed"
    except FileNotFoundError:
        capture_status, report["outcome"] = "launch_unavailable", "unavailable"
    except subprocess.TimeoutExpired:
        capture_status, report["outcome"] = "timeout", "failed"
    except OSError:
        capture_status, report["outcome"] = "launch_failed", "failed"
    report["process_observation"] = {
        "collector": "safe2.local-process.v1", "capture_status": capture_status,
        "process_exit_code": exit_code, "duration_ms": max(0, int((time.monotonic() - started) * 1000)),
        "command_sha256": hashlib.sha256(canonical_bytes(list(command))).hexdigest(),
        "stdout_sha256": stdout_hash, "stderr_sha256": stderr_hash,
        "output_complete": output_complete, "raw_output_retained": False,
    }
    if validate_artifact("tool-result-v1", report):
        raise ValueError("Collector produced an invalid report")
    return report
