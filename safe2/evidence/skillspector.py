"""Optional NVIDIA SkillSpector CLI adapter using its public JSON contract."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from safe2.bounded_process import run_bounded


def _target_digest(
    target: Path, *, max_files: int = 10_000, max_bytes: int = 100_000_000
) -> str:
    digest = hashlib.sha256()
    if target.is_symlink():
        raise RuntimeError("SkillSpector target must not be a symbolic link")
    paths = [target] if target.is_file() else sorted(path for path in target.rglob("*") if path.is_file())
    if len(paths) > max_files:
        raise RuntimeError("SkillSpector target exceeds the file-count limit")
    total = 0
    for path in paths:
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            raise RuntimeError("SkillSpector target contains a symbolic-link file")
        digest.update(str(path.relative_to(target.parent)).replace("\\", "/").encode())
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                total += len(block)
                if total > max_bytes:
                    raise RuntimeError("SkillSpector target exceeds the byte limit")
                digest.update(block)
    return digest.hexdigest()


def collect(
    target: str,
    *,
    no_llm: bool = True,
    executable: str = "skillspector",
    timeout: float = 300.0,
    max_output_bytes: int = 10_000_000,
) -> dict:
    binary = shutil.which(executable)
    if not binary:
        raise RuntimeError(
            "SkillSpector is not installed or not on PATH. Install it separately; "
            "it is an optional independent evidence provider."
        )
    target_path = Path(target).resolve()
    if not target_path.exists():
        raise RuntimeError(f"SkillSpector target does not exist: {target}")
    digest_before = _target_digest(target_path)
    command = [binary, "scan", str(target_path), "--format", "json"]
    if no_llm:
        command.append("--no-llm")
    try:
        version_result = run_bounded([binary, "--version"], timeout=10, max_bytes=4096)
        provider_version = (
            (version_result.stdout or version_result.stderr).decode("utf-8", errors="replace").strip()[:200] or "unknown"
        )
        completed = run_bounded(command, timeout=timeout, max_bytes=max_output_bytes)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"SkillSpector exceeded the {timeout:g}-second timeout") from exc
    if completed.returncode not in (0, 1):
        raise RuntimeError("SkillSpector assessment failed with an unsupported exit code")
    if completed.exceeded:
        raise RuntimeError("SkillSpector output exceeds the byte limit")
    try:
        source = json.loads(completed.stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("SkillSpector did not return valid JSON") from exc
    if not isinstance(source, dict):
        raise TypeError("SkillSpector JSON output must be an object")
    digest_after = _target_digest(target_path)
    if digest_before != digest_after:
        raise RuntimeError("SkillSpector target changed during assessment")
    return {
        "schema_version": "safe2.skillspector-evidence.v1",
        "provider": {
            "name": "NVIDIA SkillSpector",
            "mode": "static" if no_llm else "static-and-semantic",
            "version": provider_version,
            "upstream": "https://github.com/NVIDIA/SkillSpector",
            "license": "Apache-2.0",
        },
        "collected_at": datetime.now(UTC).isoformat(),
        "target": {"path": str(target_path), "sha256": digest_after},
        "source_contract": source.get("schema_version", "unversioned-json"),
        "source_result": source,
        "source_exit_code": completed.returncode,
        "attribution": "Independent evidence provider; no NVIDIA endorsement or certification is implied.",
        "conformance_claim": False,
        "limitations": [
            "Adapter compatibility is bounded to the recorded provider version and JSON output contract.",
            "Scanner findings are evidence inputs, not AI SAFE2 conformance decisions.",
        ],
    }
