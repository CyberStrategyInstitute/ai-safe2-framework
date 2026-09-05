"""Inventory and validate executable AI SAFE2 reference examples."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import click

from safe2.aism.scoring import assess
from safe2.bounded_process import run_bounded

STACK_RE = re.compile(r"<!--\s*stack:\s*(.+?)\s*-->", re.IGNORECASE)
DESC_RE = re.compile(r"<!--\s*description:\s*(.+?)\s*-->", re.IGNORECASE)


def _repo_root() -> Path:
    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "ai-safe2.manifest.json").exists():
            return root
    packaged_root = Path(__file__).resolve().parent.parent
    if (packaged_root / "examples" / "aism-decision-card" / "safe2-example.json").exists():
        return packaged_root
    raise click.ClickException("No repository or packaged AI SAFE2 examples were found.")


def inventory(root: Path) -> list[dict]:
    rows = []
    for folder in sorted((root / "examples").iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        readme = folder / "README.md"
        text = readme.read_text(encoding="utf-8", errors="replace") if readme.exists() else ""
        stack = STACK_RE.search(text)
        description = DESC_RE.search(text)
        validations = (
            list((folder / "validation").glob("*")) if (folder / "validation").is_dir() else []
        )
        rows.append(
            {
                "id": folder.name,
                "stack": stack.group(1).strip() if stack else None,
                "description": description.group(1).strip() if description else None,
                "manifest": (folder / "safe2-example.json").is_file(),
                "smoke_test": any(
                    (folder / name).is_file() for name in ("smoke_test.py", "smoke_test.js")
                ),
                "validation_artifacts": len([path for path in validations if path.is_file()]),
                "policy": (folder / "controls" / "policy.yaml").is_file(),
            }
        )
    return rows


@click.group()
def example():
    """Inspect examples as implementation and validation evidence."""


@example.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_examples(fmt: str):
    """List repository examples and their executable evidence surfaces."""
    rows = inventory(_repo_root())
    if fmt == "json":
        click.echo(json.dumps({"examples": rows}, indent=2))
        return
    click.echo("Example                          Manifest  Smoke  Validation  Policy")
    for row in rows:
        click.echo(
            f"{row['id']:<32} {row['manifest']!s:<9} {row['smoke_test']!s:<6} "
            f"{row['validation_artifacts']:<11} {row['policy']}"
        )


@example.command("verify")
@click.argument("name")
def verify_example(name: str):
    """Validate an example manifest and its declared expected assessment."""
    folder = _repo_root() / "examples" / name
    manifest_path = folder / "safe2-example.json"
    if not manifest_path.is_file():
        raise click.ClickException(f"{name} has no safe2-example.json manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for field in ("schema_version", "id", "stack", "status", "framework_version", "expected"):
        if field not in manifest:
            errors.append(f"missing {field}")
    if manifest.get("id") != name:
        errors.append("manifest id does not match folder name")
    assessment_path = folder / "assessment.json"
    observed = None
    if assessment_path.is_file():
        result = assess(json.loads(assessment_path.read_text(encoding="utf-8")))
        observed = {
            "decision": result["decision"]["disposition"],
            "completeness": result["score"]["completeness"],
        }
        expected = manifest.get("expected", {})
        for key in ("decision", "completeness"):
            if key in expected and expected[key] != observed[key]:
                errors.append(f"expected {key}={expected[key]!r}, observed {observed[key]!r}")
    elif (folder / "smoke_test.py").is_file():
        try:
            completed = run_bounded(
                [sys.executable, str(folder / "smoke_test.py")],
                timeout=120,
                max_bytes=1_000_000,
            )
            if completed.exceeded:
                errors.append("smoke test output exceeded the byte limit")
            elif completed.returncode != 0:
                errors.append(f"smoke test failed with exit code {completed.returncode}")
            else:
                candidate = json.loads(completed.stdout.decode("utf-8"))
                if not isinstance(candidate, dict):
                    errors.append("smoke test result must be a JSON object")
                else:
                    observed = candidate
                    for key, value in manifest.get("expected", {}).items():
                        if observed.get(key) != value:
                            errors.append(
                                f"expected {key}={value!r}, observed {observed.get(key)!r}"
                            )
        except (OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            errors.append(f"smoke test could not be verified ({type(exc).__name__})")
    if errors:
        raise click.ClickException("; ".join(errors))
    click.echo(json.dumps({"example": name, "status": "verified", "observed": observed}, indent=2))
