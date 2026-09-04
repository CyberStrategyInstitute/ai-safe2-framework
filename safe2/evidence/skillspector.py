"""Optional NVIDIA SkillSpector CLI adapter using its public JSON contract."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def _target_digest(target: Path) -> str:
    digest = hashlib.sha256()
    paths = [target] if target.is_file() else sorted(path for path in target.rglob("*") if path.is_file())
    for path in paths:
        if ".git" in path.parts:
            continue
        digest.update(str(path.relative_to(target.parent)).replace("\\", "/").encode())
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def collect(
    target: str, *, no_llm: bool = True, executable: str = "skillspector", timeout: float = 300.0
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
    command = [binary, "scan", str(target_path), "--format", "json"]
    if no_llm:
        command.append("--no-llm")
    try:
        version_result = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, check=False, timeout=10
        )
        provider_version = (version_result.stdout or version_result.stderr).strip() or "unknown"
        completed = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"SkillSpector exceeded the {timeout:g}-second timeout") from exc
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr.strip() or "SkillSpector assessment failed")
    try:
        source = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("SkillSpector did not return valid JSON") from exc
    return {
        "schema_version": "1.0",
        "provider": {
            "name": "NVIDIA SkillSpector",
            "mode": "static" if no_llm else "static-and-semantic",
            "version": provider_version,
            "upstream": "https://github.com/NVIDIA/SkillSpector",
            "license": "Apache-2.0",
        },
        "collected_at": datetime.now(UTC).isoformat(),
        "target": {"path": str(target_path), "sha256": _target_digest(target_path)},
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
