"""Capture operational agent friction as structured evaluation evidence."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.evidence.friction import (
    CATEGORIES,
    OUTCOMES,
    append_event,
    record_event,
    summarize_events,
)

DEFAULT_LOG = Path(".safe2/evidence/friction.jsonl")


@click.group("feedback")
def feedback() -> None:
    """Record privacy-safe LLM and agent workflow friction."""


@feedback.command("verify-pytest")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.pass_context
def verify_pytest_command(ctx: click.Context, source: Path) -> None:
    """Recheck capture consistency without execution. Exit 0 is NOT a passing-test gate."""
    from safe2.challenge.io import parse_json, read_bytes
    from safe2.evidence.pytest_capture import verify_pytest_capture

    try:
        result = verify_pytest_capture(parse_json(read_bytes(source, limit=1_000_000)))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Capture could not be read: invalid or unavailable input") from exc
    click.echo(json.dumps(result, allow_nan=False))
    if not result["internally_consistent"]:
        ctx.exit(1)


@feedback.command("capture-pytest")
@click.option("--execute", required=True, is_flag=True)
@click.option("--python", "python_path", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--cwd", required=True, type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--task-id", required=True)
@click.option("--revision", required=True)
@click.option("--environment", required=True)
@click.option("--call-id", required=True)
@click.option("--timeout", type=click.IntRange(1, 3600), default=60)
@click.option("--output", required=True, type=click.Path(path_type=Path))
@click.argument("targets", nargs=-1, required=True)
@click.pass_context
def capture_pytest_command(ctx: click.Context, execute: bool, python_path: Path, cwd: Path,
                           task_id: str, revision: str, environment: str, call_id: str,
                           timeout: int, output: Path, targets: tuple[str, ...]) -> None:
    """Run selected tests and bind fresh JUnit to observed process exit. NOT a sandbox.

    Requires absolute --python. Exit 0 means all reported tests passed without skips;
    nonzero means failure, incomplete evidence, or an error. Never proves task completion.
    """
    import os

    from safe2.challenge.io import safe_path
    from safe2.evidence.pytest_capture import capture_pytest

    if not execute:
        raise click.ClickException("Explicit execution authorization required")
    try:
        descriptor = os.open(safe_path(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            result = capture_pytest(python=python_path, cwd=cwd, targets=targets, task_id=task_id,
                                    revision=revision, environment=environment, call_id=call_id, timeout=timeout)
            handle.write((json.dumps(result, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Pytest capture failed; output may be incomplete and tests may have run") from exc
    click.echo(json.dumps(result["all_tests_passed_claim"]))
    if result["all_tests_passed_claim"]["status"] != "supported":
        ctx.exit(1)


@feedback.command("usage")
@click.argument("sources", nargs=-1, required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", type=click.Path(path_type=Path), default=None)
def usage_command(sources: tuple[Path, ...], output: Path | None) -> None:
    """Correlate task INPUT declarations; no artifact execution or billing verification."""
    from safe2.challenge.io import parse_json, read_bytes, write_json
    from safe2.evidence.usage import correlate_usage

    try:
        if len(sources) > 32:
            raise ValueError("At most 32 inputs per accounting batch")
        result = correlate_usage([parse_json(read_bytes(source, limit=1_000_000)) for source in sources])
        if output is not None:
            write_json(output, result)
        else:
            click.echo(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Usage correlation failed: invalid/ambiguous inputs or unavailable output") from exc


@feedback.command("import-junit")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--task-id", required=True)
@click.option("--revision", required=True)
@click.option("--environment", required=True)
@click.option("--exit-code", required=True, type=click.IntRange(0, 255))
@click.option("--output", required=True, type=click.Path(path_type=Path))
def import_junit_command(source: Path, task_id: str, revision: str, environment: str,
                         exit_code: int, output: Path) -> None:
    """Normalize supported JUnit XML; exit 0 means import succeeded, NOT tests passed.

    Exit code and run context are operator-supplied, not authenticated here.
    """
    from safe2.challenge.io import read_bytes, write_json
    from safe2.evidence.junit import import_junit

    try:
        report = import_junit(read_bytes(source, limit=1_000_000), task_id=task_id,
                              revision=revision, environment=environment, exit_code=exit_code)
        write_json(output, report)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("JUnit import failed: unsupported/invalid report, metadata, or output") from exc
    click.echo(json.dumps({"counts": report["counts"], "execution_verified": False}))


@feedback.command("capture-process")
@click.option("--execute", is_flag=True, required=True, help="Explicitly authorize running the supplied command. NOT a sandbox.")
@click.option("--cwd", required=True, type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--task-id", required=True)
@click.option("--revision", required=True, help="Operator-declared revision; not independently checked.")
@click.option("--environment", required=True)
@click.option("--call-id", required=True)
@click.option("--tool", required=True)
@click.option("--timeout", type=click.IntRange(1, 3600), default=60, show_default=True)
@click.option("--max-bytes", type=click.IntRange(1, 10_000_000), default=1_000_000, show_default=True)
@click.option("--output", required=True, type=click.Path(path_type=Path))
@click.argument("command", nargs=-1, type=click.UNPROCESSED, required=True)
@click.pass_context
def capture_process_command(ctx: click.Context, execute: bool, cwd: Path, task_id: str,
                            revision: str, environment: str, call_id: str, tool: str,
                            timeout: int, max_bytes: int, output: Path, command: tuple[str, ...]) -> None:
    """Observe an explicit command after --, using an absolute executable path.

    Executes with your user permissions; no network/filesystem or descendant isolation.
    Exit 0: process completed with exit 0 and complete output capture. NOT proof tests passed.
    Other outcomes exit 1. Raw argv/output are not retained; report is unsigned.
    """
    import os

    from safe2.challenge.io import safe_path
    from safe2.evidence.process_capture import capture_process

    if not execute:
        raise click.ClickException("Explicit --execute authorization is required")
    try:
        # Reserve output before execution: existing/unwritable targets prevent launch.
        target = safe_path(output)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            report = capture_process(command, cwd=cwd, task_id=task_id, revision=revision,
                                     environment=environment, call_id=call_id, tool=tool,
                                     timeout=timeout, max_bytes=max_bytes)
            handle.write((json.dumps(report, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Capture failed; output may be incomplete. Do not assume the command did not run.") from exc
    click.echo(json.dumps({"outcome": report["outcome"],
                           "capture_status": report["process_observation"]["capture_status"],
                           "completion_verified": False}))
    if report["outcome"] != "succeeded":
        ctx.exit(1)


@feedback.command("receipt")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--artifact-root", required=True, type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--format", "output_format", type=click.Choice(["json", "markdown"]), default="json")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
@click.option("--trusted-public-key", type=click.Path(path_type=Path, exists=True, dir_okay=False), default=None)
@click.option("--require-authentication", is_flag=True, help="Require trusted signatures for test/tool report criteria, not plain artifact hashes.")
def task_receipt(source: Path, artifact_root: Path, output_format: str, output: Path | None,
                 trusted_public_key: Path | None, require_authentication: bool) -> None:
    """Check artifact hashes and test/tool reports; NOT a completion or billing gate.

    Exit 0 means a receipt was produced, including contradicted/unverifiable results.
    Output files must not already exist. No target code is executed.
    """
    from safe2.challenge.io import read_json, write_text
    from safe2.evidence.task_receipt import evaluate_task, render_receipt

    try:
        receipt = evaluate_task(read_json(source), artifact_root,
                                trusted_public_key=trusted_public_key,
                                require_authentication=require_authentication)
        body = (render_receipt(receipt) if output_format == "markdown"
                else json.dumps(receipt, indent=2, allow_nan=False) + "\n")
        if output is not None:
            write_text(output, body)
        else:
            click.echo(body, nl=False)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Receipt could not be produced: invalid input or unsafe/unavailable I/O") from exc


@feedback.command("sign-report")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--private-key", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--signer-id", required=True)
@click.option("--ttl", type=click.IntRange(1, 86400), default=3600, show_default=True)
@click.option("--output", required=True, type=click.Path(path_type=Path))
def sign_report_command(source: Path, private_key: Path, signer_id: str, ttl: int, output: Path) -> None:
    """Sign test/tool report bytes. Does NOT run tests, approve content, or prove execution."""
    from safe2.challenge.io import read_bytes, write_json
    from safe2.evidence.report_auth import sign_report

    try:
        result = sign_report(read_bytes(source, limit=1_000_000), private_key, signer_id, ttl)
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Signing failed; check the report, Ed25519 key, output, and challenge extra") from exc
    click.echo("Detached signature written; report execution is not authenticated.")


@feedback.command("verify-report")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.argument("attestation", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--trusted-public-key", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.pass_context
def verify_report_command(ctx: click.Context, source: Path, attestation: Path, trusted_public_key: Path) -> None:
    """Verify origin/integrity/freshness only: exit 0 authenticated, nonzero otherwise."""
    from safe2.challenge.io import parse_json, read_bytes
    from safe2.evidence.report_auth import verify_report

    try:
        status = verify_report(read_bytes(source, limit=1_000_000),
                               parse_json(read_bytes(attestation, limit=16384)), trusted_public_key)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Authentication could not be checked; invalid or unavailable input/key/crypto") from exc
    click.echo(json.dumps({"authentication": status, "execution_verified": False, "conformance_claim": False}))
    if status != "authenticated_trusted_key":
        ctx.exit(1)


@feedback.command("record")
@click.option("--category", type=click.Choice(sorted(CATEGORIES)), required=True)
@click.option("--outcome", type=click.Choice(sorted(OUTCOMES)), required=True)
@click.option("--severity", type=click.Choice(["low", "medium", "high", "critical"]), required=True)
@click.option("--summary", required=True, help="Short sanitized description; do not include secrets or prompt contents.")
@click.option("--harness", default=None)
@click.option("--environment", default=None)
@click.option("--evidence-ref", multiple=True, help="Reference to external verification, not raw sensitive output.")
@click.option("--resolved/--unresolved", default=False)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=DEFAULT_LOG, show_default=True)
def record_feedback(
    category: str,
    outcome: str,
    severity: str,
    summary: str,
    harness: str | None,
    environment: str | None,
    evidence_ref: tuple[str, ...],
    resolved: bool,
    output: Path,
) -> None:
    """Append one sanitized friction event to a local JSONL evidence log."""
    try:
        event = record_event(
            category=category,
            outcome=outcome,
            severity=severity,
            summary=summary,
            harness=harness,
            environment=environment,
            evidence_refs=evidence_ref,
            resolved=resolved,
        )
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    try:
        append_event(output, event)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(event, indent=2))


@feedback.command("summary")
@click.argument("source", type=click.Path(path_type=Path, dir_okay=False, exists=True), default=DEFAULT_LOG)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
@click.option("--max-bytes", default=20_000_000, type=click.IntRange(1, 100_000_000), show_default=True)
def feedback_summary(source: Path, output: Path | None, max_bytes: int) -> None:
    """Summarize friction and the claimed-versus-verified completion gap."""
    try:
        result = summarize_events(source, max_bytes=max_bytes)
    except (OSError, TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    body = json.dumps(result, indent=2) + "\n"
    if output:
        if output.is_symlink():
            raise click.ClickException("summary output must not be a symbolic link")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body, encoding="utf-8")
        click.echo(f"Friction summary: {output}")
    else:
        click.echo(body, nl=False)
