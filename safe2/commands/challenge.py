"""Offline challenge fixtures and provider-neutral evidence workflows."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click


def _json(value: Any) -> None:
    click.echo(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False))


def _execute(ctx: click.Context, operation: str, action: Callable[[], Any]) -> Any:
    try:
        return action()
    except (ValueError, OSError, TypeError, KeyError, ImportError) as exc:
        # Input values and exception messages can contain source secrets.
        _json({
            "schema_version": "safe2.challenge-command.v1",
            "valid": False,
            "operation": operation,
            "error": type(exc).__name__,
            "hint": (
                "Check the published contract, input limits and a new safe output path. "
                "Signing requires the challenge extra and PEM Ed25519 keys."
            ),
            "instance_values_emitted": False,
        })
        ctx.exit(2)


def _write(value: dict, output: Path, operation: str) -> None:
    from safe2.challenge.io import write_json

    write_json(output, value)
    _json({
        "schema_version": "safe2.challenge-command.v1",
        "operation": operation,
        "output": str(output),
        "artifact_schema": value["schema_version"],
        "run_id": value.get("run_id"),
        "comparable": value.get("comparable"),
    })


@click.group("challenge")
def challenge() -> None:
    """Run fixtures or authorized processes; translate and verify evidence.

    The execute command starts only a pre-registered process after an explicit
    authorization flag. It is bounded but not sandboxed. Translation and
    matching outcomes do not establish independent replication.
    """


@challenge.command("quickstart")
@click.argument("challenge_id", type=click.Choice(["001"]))
@click.option("--output-dir", type=click.Path(path_type=Path), required=True)
@click.pass_context
def quickstart(ctx: click.Context, challenge_id: str, output_dir: Path) -> None:
    """Create and verify a new offline starter bundle with readable Decision Cards."""
    from safe2.challenge.bundle import quickstart as create

    _json(_execute(ctx, "quickstart", lambda: create(output_dir, challenge_id)))


@challenge.command("verify-bundle")
@click.argument("directory", type=click.Path(path_type=Path))
@click.option("--expected-sha256", default=None, help="Manifest fingerprint obtained from a trusted source.")
@click.pass_context
def verify_bundle(ctx: click.Context, directory: Path, expected_sha256: str | None) -> None:
    """Check a portable starter folder without executing any submitted code."""
    from safe2.challenge.bundle import verify_bundle as verify

    result = _execute(ctx, "verify-bundle", lambda: verify(directory, expected_sha256))
    _json(result)
    if not result["valid"]:
        ctx.exit(1)


@challenge.command("list")
@click.pass_context
def list_challenges(ctx: click.Context) -> None:
    """Discover the packaged offline Challenge 001 protocol."""
    from safe2.challenge.protocol import protocol

    specification = _execute(ctx, "list", protocol)
    _json({
        "schema_version": "safe2.challenge-catalog.v1",
        "challenges": [{
            "id": "001",
            "protocol_id": specification["id"],
            "protocol_version": specification["version"],
            "execution": "inert_dictionary_fixture",
            "scenario_count": len(specification["scenarios"]),
            "live_agent_execution": False,
            "controlled_process_execution": True,
        }],
    })


@challenge.command("validate")
@click.argument("challenge_id", type=click.Choice(["001"]))
@click.pass_context
def validate_challenge(ctx: click.Context, challenge_id: str) -> None:
    """Validate packaged protocol identity; not a conformance verdict."""
    from safe2.challenge.protocol import experiment, protocol

    specification, identity = _execute(ctx, "validate", lambda: (protocol(), experiment()))
    _json({
        "schema_version": "safe2.challenge-protocol-validation.v1",
        "valid": True,
        "challenge_id": challenge_id,
        "experiment": identity,
        "scenario_count": len(specification["scenarios"]),
        "framework_profile_conformance": "not_assessed",
        "limitations": ["Packaged fixture identity only; no live deployment was assessed."],
    })


@challenge.command("run")
@click.argument("challenge_id", type=click.Choice(["001"]))
@click.option("--seed", default=0, type=click.IntRange(0, 2_147_483_647), show_default=True)
@click.option("--repetitions", default=1, type=click.IntRange(1, 100), show_default=True)
@click.option(
    "--treatment", "treatments", multiple=True,
    type=click.Choice(["uncontrolled", "conventional", "safe2-reference"]),
    help="Repeat to select treatments; omitted runs all three.",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True)
@click.pass_context
def run_challenge(
    ctx: click.Context, challenge_id: str, seed: int, repetitions: int,
    treatments: tuple[str, ...], output: Path,
) -> None:
    """Execute the safe, deterministic state fixture; always use a new output."""
    from safe2.challenge.runner import run_challenge as run

    def action() -> None:
        result = run(challenge_id, seed=seed, repetitions=repetitions, treatments=list(treatments) or None)
        _write(result, output, "run")

    _execute(ctx, "run", action)


@challenge.command("plan")
@click.argument("challenge_id", type=click.Choice(["001"]))
@click.option("--executable", type=click.Path(path_type=Path, dir_okay=False), required=True)
@click.option("--arg", "arguments", multiple=True, help="Repeat for each literal executor argument.")
@click.option("--provider-name", required=True)
@click.option("--provider-version", required=True)
@click.option("--producer-id", required=True)
@click.option("--treatment", required=True)
@click.option("--seed", default=0, type=click.IntRange(0, 2_147_483_647), show_default=True)
@click.option("--repetitions", default=1, type=click.IntRange(1, 100), show_default=True)
@click.option("--timeout-seconds", default=30.0, type=click.FloatRange(0.1, 300), show_default=True)
@click.option("--max-output-bytes", default=262_144, type=click.IntRange(1024, 10_485_760), show_default=True)
@click.option("--system-identity", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--output", "output", type=click.Path(path_type=Path), required=True)
@click.pass_context
def plan_execution(
    ctx: click.Context, challenge_id: str, executable: Path, arguments: tuple[str, ...],
    provider_name: str, provider_version: str, producer_id: str, treatment: str,
    seed: int, repetitions: int, timeout_seconds: float, max_output_bytes: int,
    system_identity: Path | None, output: Path,
) -> None:
    """Pre-register an exact Challenge 001 executor without running it."""
    from safe2.challenge.execution import create_plan

    def action() -> None:
        value = create_plan(
            [str(executable), *arguments], provider_name=provider_name,
            provider_version=provider_version, producer_id=producer_id,
            treatment=treatment, seed=seed, repetitions=repetitions,
            timeout_seconds=timeout_seconds, max_output_bytes=max_output_bytes,
            system_identity=system_identity,
        )
        _write(value, output, "plan")

    _execute(ctx, "plan", action)


@challenge.command("execute")
@click.argument("plan", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--output-dir", type=click.Path(path_type=Path), required=True)
@click.option(
    "--authorize-process-execution", is_flag=True, required=True,
    help="Confirm the named external process may run with current-user authority.",
)
@click.pass_context
def execute_controlled(
    ctx: click.Context, plan: Path, output_dir: Path, authorize_process_execution: bool,
) -> None:
    """Run a pre-registered executor; bounded process I/O is not a sandbox."""
    from safe2.challenge.execution import execute_plan
    from safe2.challenge.io import read_json, safe_path, write_json

    def action() -> None:
        if not authorize_process_execution:
            raise ValueError("Explicit process execution authorization is required.")
        destination = safe_path(output_dir)
        if destination.exists():
            raise FileExistsError("Output directory already exists.")
        source, run, receipt = execute_plan(read_json(plan))
        destination.mkdir(parents=True, exist_ok=False)
        write_json(destination / "challenge-source.json", source)
        write_json(destination / "challenge-run.json", run)
        write_json(destination / "execution-receipt.json", receipt)
        _json({
            "schema_version": "safe2.challenge-command.v1", "operation": "execute",
            "output_dir": str(destination), "run_id": run["run_id"],
            "episodes": run["summary"]["episodes"],
            "incomplete": run["summary"]["status_counts"]["incomplete"],
            "process_sandboxed": False, "descendant_containment": False,
            "independent_replication": "not_established",
        })

    _execute(ctx, "execute", action)


@challenge.command("verify-execution")
@click.argument("directory", type=click.Path(path_type=Path, file_okay=False))
@click.option("--plan", "plan_path", type=click.Path(path_type=Path, dir_okay=False), required=True)
@click.option("--system-identity", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.pass_context
def verify_controlled(
    ctx: click.Context, directory: Path, plan_path: Path, system_identity: Path | None,
) -> None:
    """Verify plan, source, run, receipt, and optional identity bindings."""
    from safe2.challenge.execution import verify_execution
    from safe2.challenge.io import read_json, safe_path

    def action() -> dict:
        root = safe_path(directory)
        return verify_execution(
            read_json(plan_path), read_json(root / "challenge-source.json"),
            read_json(root / "challenge-run.json"), read_json(root / "execution-receipt.json"),
            system_identity=system_identity,
        )

    result = _execute(ctx, "verify-execution", action)
    _json(result)
    if not result["valid"]:
        ctx.exit(1)


@challenge.command("example")
@click.option("--provider", type=click.Choice(["tenir"]), default="tenir", show_default=True)
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True)
@click.pass_context
def example_source(ctx: click.Context, provider: str, output: Path) -> None:
    """Export an explicitly synthetic TENIR adapter specimen, not TENIR output."""
    from safe2.challenge.adapters import example_source as example

    _execute(ctx, "example", lambda: _write(example(), output, "example"))


@challenge.command("import")
@click.argument("source", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--adapter", type=click.Choice(["generic", "tenir"]), default="generic", show_default=True)
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True)
@click.pass_context
def import_source(ctx: click.Context, source: Path, adapter: str, output: Path) -> None:
    """Translate a bounded offline export; preserve original provider records."""
    from safe2.challenge.adapters import import_source as translate
    from safe2.challenge.io import parse_json, read_bytes

    def action() -> None:
        raw = read_bytes(source)
        document = parse_json(raw)
        fingerprint = hashlib.sha256(raw).hexdigest()
        _write(translate(document, adapter=adapter, source_sha256=fingerprint), output, "import")

    _execute(ctx, "import", action)


@challenge.command("compare")
@click.argument("left", type=click.Path(path_type=Path, dir_okay=False))
@click.argument("right", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True)
@click.pass_context
def compare_runs(ctx: click.Context, left: Path, right: Path, output: Path) -> None:
    """Compare matched experiments; exit 1 if incompatible (artifact retained)."""
    from safe2.challenge.compare import compare_runs as compare
    from safe2.challenge.io import read_json

    result = _execute(ctx, "compare", lambda: compare(read_json(left), read_json(right)))
    _execute(ctx, "compare", lambda: _write(result, output, "compare"))
    if not result["comparable"]:
        ctx.exit(1)


@challenge.command("verify")
@click.argument("source", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--public-key", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--require-signature", is_flag=True)
@click.option("--left-run", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--right-run", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.option("--source-export", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.pass_context
def verify_run(
    ctx: click.Context, source: Path, public_key: Path | None, require_signature: bool,
    left_run: Path | None, right_run: Path | None, source_export: Path | None,
) -> None:
    """Regrade and check a run's seal; verify signatures only with your trusted key."""
    from safe2.challenge.io import read_json
    from safe2.challenge.model import verify_comparison
    from safe2.challenge.model import verify_run as verify

    def action() -> dict:
        artifact = read_json(source)
        if artifact.get("schema_version") == "safe2.challenge-comparison.v1":
            if public_key or require_signature or source_export or bool(left_run) != bool(right_run):
                raise ValueError("comparison_verification_options_invalid")
            return verify_comparison(
                artifact,
                left=read_json(left_run) if left_run else None,
                right=read_json(right_run) if right_run else None,
            )
        if left_run or right_run:
            raise ValueError("run_verification_options_invalid")
        return verify(
            artifact, public_key=public_key, require_signature=require_signature,
            source_export=source_export,
        )

    result = _execute(ctx, "verify", action)
    _json(result)
    if not result["valid"]:
        ctx.exit(1)


@challenge.command("report")
@click.argument("source", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--format", "format_name", type=click.Choice(["markdown", "html"]), default="markdown", show_default=True)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
@click.pass_context
def report_run(ctx: click.Context, source: Path, format_name: str, output: Path | None) -> None:
    """Produce a readable Decision Card with facts, gaps and next actions."""
    from safe2.challenge.io import read_json, write_text
    from safe2.challenge.model import verify_comparison
    from safe2.challenge.model import verify_run as verify
    from safe2.challenge.report import render_report

    run = _execute(ctx, "report", lambda: read_json(source))
    verifier = verify_comparison if run.get("schema_version") == "safe2.challenge-comparison.v1" else verify
    verification = _execute(ctx, "report", lambda: verifier(run))
    if not verification["valid"]:
        _json(verification)
        ctx.exit(1)
    body = _execute(ctx, "report", lambda: render_report(run, format_name=format_name))
    if output is None:
        click.echo(body, nl=False)
    else:
        _execute(ctx, "report", lambda: write_text(output, body))
        _json({"schema_version": "safe2.challenge-command.v1", "operation": "report", "output": str(output)})


@challenge.command("sign")
@click.argument("source", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--key", "key_path", type=click.Path(path_type=Path, dir_okay=False), required=True)
@click.option("--signer-id", required=True, help="Signer label bound to this artifact, not proof of authority.")
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True)
@click.pass_context
def sign_run(ctx: click.Context, source: Path, key_path: Path, signer_id: str, output: Path) -> None:
    """Sign a verified artifact; not upstream attestation or human action approval."""
    from safe2.challenge.integrity import sign_run as sign
    from safe2.challenge.io import read_json

    _execute(ctx, "sign", lambda: _write(sign(read_json(source), key_path, signer_id), output, "sign"))
