"""Unified project assessment command."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import click

from safe2.assessment import AssessmentError, run_assessment
from safe2.manifest import post as manifest_post
from safe2.manifest.collect import ManifestCollectionError, ManifestValidationError
from safe2.manifest.post import (
    UNSIGNED_NOTICE,
    PostError,
    PostOutcome,
    describe_outcome,
    manual_call_hint,
    post_manifest,
    require_key,
)
from safe2.manifest.workflow import ManifestArtifact, build_and_write
from safe2.secure_io import PublishedCleanupError


@click.command("assess")
@click.argument(
    "target", default=".", type=click.Path(path_type=Path, file_okay=False, exists=True)
)
@click.option("--output-dir", type=click.Path(path_type=Path), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--scan-content",
    is_flag=True,
    help="Consent to bounded local project-content reads for static analysis.",
)
@click.option(
    "--inspect-config",
    is_flag=True,
    help="Emit redacted structural configuration evidence; requires content consent.",
)
@click.option(
    "--wsl/--no-wsl", default=False, help="Inventory WSL distribution names when available."
)
@click.option(
    "--manifest",
    is_flag=True,
    help=(
        "Also write aisafe2-project-manifest/1 (names, flags, counts, digests only). "
        "Requires --scan-content and --inspect-config. Sends nothing."
    ),
)
@click.option(
    "--manifest-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="With --manifest, write the manifest here instead of inside the evidence bundle.",
)
@click.option(
    "--post",
    is_flag=True,
    help=(
        "With --manifest, send the manifest to hosted Tarvin. The Tarvin key is read only "
        "from the SAFE2_MCP_PRO_KEY environment variable."
    ),
)
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human")
def assess_command(
    target: Path,
    output_dir: Path | None,
    config_path: Path | None,
    scan_content: bool,
    inspect_config: bool,
    wsl: bool,
    manifest: bool,
    manifest_out: Path | None,
    post: bool,
    fmt: str,
) -> None:
    """Create one reviewable environment and project evidence bundle."""
    key: str | None = None
    if manifest:
        # Consent is checked before anything is read, written, or sent.
        if not (scan_content and inspect_config):
            raise click.ClickException(
                "--manifest requires explicit --scan-content and --inspect-config consent"
            )
        if post:
            try:
                key = require_key(dict(os.environ))
            except PostError as exc:
                raise click.ClickException(str(exc)) from exc
    elif manifest_out is not None or post:
        raise click.UsageError("--manifest-out and --post require --manifest")
    try:
        result = run_assessment(
            target,
            output_dir=output_dir,
            config_path=config_path,
            scan_content=scan_content,
            inspect_config=inspect_config,
            include_wsl=wsl,
        )
    except (AssessmentError, OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    produced: ManifestArtifact | None = None
    outcome: PostOutcome | None = None
    if manifest:
        try:
            produced = build_and_write(
                target.resolve(),
                bundle_dir=Path(result["output_dir"]),
                config_path=config_path,
                manifest_out=manifest_out,
            )
        except PublishedCleanupError as exc:
            raise click.ClickException(
                f"The manifest was written to {exc.path} and is complete, but its staging file "
                f"{exc.temporary} could not be removed ({exc.__cause__}). The collection notes were kept "
                f"in {result['output_dir']}. Remove the leftover file by hand. Nothing was sent."
            ) from exc
        except (ManifestCollectionError, ManifestValidationError, OSError, ValueError) as exc:
            raise click.ClickException(
                f"{exc}. The evidence bundle was kept at {result['output_dir']} and no manifest "
                "was written; fix the cause and rerun with a new --output-dir."
            ) from exc
        if post and key is not None:
            try:
                outcome = post_manifest(produced.manifest, key=key)
            except PostError as exc:
                raise click.ClickException(
                    f"{exc}. The manifest was written to {produced.path} and was not sent."
                ) from exc

    if fmt == "json":
        payload = dict(result)
        if produced is not None:
            payload["manifest"] = _manifest_summary(produced)
            payload["post"] = _post_summary(produced, post, key, outcome)
        click.echo(json.dumps(payload, indent=2))
    else:
        summary = result["assessment"]["summary"]
        click.echo("AI SAFE2 Project Assessment")
        click.echo(f"Disposition: {summary['disposition']}")
        click.echo(f"Evidence confidence: {summary['evidence_confidence']}")
        click.echo(f"Harnesses detected: {summary['harnesses_detected']}")
        click.echo(f"Environment findings: {summary['environment_findings']}")
        click.echo(
            f"Static violations: {summary['static_violations'] if summary['static_violations'] is not None else 'NOT ASSESSED'}"
        )
        click.echo(f"Evidence bundle: {result['output_dir']}")
        if produced is not None:
            _echo_manifest(produced, post, key, outcome)
    if outcome is not None and not outcome.succeeded:
        raise SystemExit(1)


def _manifest_summary(produced: ManifestArtifact) -> dict[str, Any]:
    return {
        "path": str(produced.path),
        "sha256": produced.sha256,
        "manifest_version": produced.manifest["manifest_version"],
        "agents": len(produced.manifest["agents"]),
        "mcp_servers": len(produced.manifest["mcp_servers"]),
        "config_files": len(produced.manifest.get("config_files", [])),
        "schema_validated": True,
        "signed": False,
        "collection_notes": str(produced.notes_path),
    }


def _post_summary(
    produced: ManifestArtifact, post: bool, key: str | None, outcome: PostOutcome | None
) -> dict[str, Any]:
    if not post:
        return {"requested": False, "sent": False}
    if outcome is None:
        return {
            "requested": True,
            "sent": False,
            "status": "skipped_no_key",
            "unsigned_notice": UNSIGNED_NOTICE,
            "manual_call": manual_call_hint(produced.path)[-1],
        }
    return {
        "requested": True,
        "sent": True,
        "endpoint": manifest_post.ENDPOINT,
        "status": outcome.status,
        "http_status": outcome.http_status,
        "attempts": outcome.attempts,
        "unsigned_notice": UNSIGNED_NOTICE,
        "result": outcome.structured,
        "error": outcome.error,
    }


def _echo_manifest(
    produced: ManifestArtifact, post: bool, key: str | None, outcome: PostOutcome | None
) -> None:
    manifest = produced.manifest
    click.echo("")
    click.echo("AI SAFE2 Project Manifest (aisafe2-project-manifest/1)")
    click.echo(
        f"Agents: {len(manifest['agents'])}; MCP servers: {len(manifest['mcp_servers'])}; "
        f"config files scanned: {len(manifest.get('config_files', []))}"
    )
    click.echo(f"Manifest: {produced.path}")
    click.echo(f"Collection notes (local only): {produced.notes_path}")
    if not post:
        click.echo("Nothing was sent. Add --post to send it to hosted Tarvin.")
        return
    click.echo(UNSIGNED_NOTICE)
    if outcome is None:
        for line in manual_call_hint(produced.path):
            click.echo(line)
        return
    for line in describe_outcome(outcome):
        click.echo(line)
