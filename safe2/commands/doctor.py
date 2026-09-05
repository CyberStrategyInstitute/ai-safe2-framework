"""Discover local harness and execution-environment surfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from safe2.discovery import (
    assess_posture,
    compare_discovery,
    discover_local,
    evaluate_policy,
    inspect_inventory,
    inventory_assets,
    load_baseline,
    load_policy,
    probe_ssh,
    probe_wsl,
    render_environment_html,
    render_environment_markdown,
    seal_inventory,
)


@click.command("doctor")
@click.argument("target", default=".", type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human", show_default=True)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
@click.option("--wsl/--no-wsl", default=True, help="Inventory installed WSL distributions when available.")
@click.option("--wsl-distro", multiple=True, help="Explicit WSL distribution to inspect; repeatable.")
@click.option("--ssh-host", multiple=True, help="Explicit [user@]host to inspect using non-interactive SSH; repeatable.")
@click.option("--ssh-port", default=22, type=click.IntRange(1, 65535), show_default=True)
@click.option("--assess/--inventory-only", default=False, help="Derive scoped posture findings from inventory metadata.")
@click.option("--assets/--no-assets", default=True, help="Inventory security-relevant project asset metadata.")
@click.option("--max-files", default=50_000, type=click.IntRange(1, 1_000_000), show_default=True)
@click.option("--hash-assets", is_flag=True, help="Opt in to local hashing of security-relevant assets for stronger drift detection.")
@click.option("--max-asset-hash-bytes", default=10_000_000, type=click.IntRange(1, 100_000_000), show_default=True)
@click.option("--inspect-config", is_flag=True, help="Opt in to redacted structural inspection of discovered JSON/TOML agent configs.")
@click.option("--max-config-bytes", default=1_048_576, type=click.IntRange(1, 100_000_000), show_default=True)
@click.option("--baseline", type=click.Path(path_type=Path, dir_okay=False, exists=True), default=None, help="Compare with a prior safe2.discovery.v1 JSON inventory.")
@click.option("--card-format", type=click.Choice(["markdown", "html"]), default=None, help="Render a human environment Decision Card; requires --assess and --card-output.")
@click.option("--card-output", type=click.Path(path_type=Path), default=None)
@click.option("--policy", type=click.Path(path_type=Path, dir_okay=False, exists=True), default=None, help="Evaluate a safe2.environment-policy.v1 policy; requires --assess.")
@click.option("--enforce-policy", is_flag=True, help="Exit 1 on DENY or 2 on HOLD after writing requested artifacts.")
@click.option("--timeout", default=5.0, type=click.FloatRange(min=0.1), show_default=True)
def doctor(
    target: Path,
    fmt: str,
    output: Path | None,
    wsl: bool,
    wsl_distro: tuple[str, ...],
    ssh_host: tuple[str, ...],
    ssh_port: int,
    assess: bool,
    assets: bool,
    max_files: int,
    hash_assets: bool,
    max_asset_hash_bytes: int,
    inspect_config: bool,
    max_config_bytes: int,
    baseline: Path | None,
    card_format: str | None,
    card_output: Path | None,
    policy: Path | None,
    enforce_policy: bool,
    timeout: float,
) -> None:
    """Inventory local agent harnesses and execution environments without reading secrets."""
    if bool(card_format) != bool(card_output):
        raise click.ClickException("--card-format and --card-output must be supplied together")
    if card_format and not assess:
        raise click.ClickException("--card-format requires --assess")
    if policy and not assess:
        raise click.ClickException("--policy requires --assess")
    if enforce_policy and not policy:
        raise click.ClickException("--enforce-policy requires --policy")
    result = discover_local(target, include_wsl=wsl, timeout=timeout)
    explicit_targets: list[dict[str, Any]] = []
    try:
        explicit_targets.extend(probe_wsl(name, timeout=timeout) for name in wsl_distro)
        explicit_targets.extend(
            probe_ssh(host, port=ssh_port, timeout=timeout) for host in ssh_host
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    result["targets"] = explicit_targets
    result["summary"]["explicit_targets"] = len(explicit_targets)
    result["summary"]["targets_completed"] = sum(
        row["status"] == "completed" for row in explicit_targets
    )
    result["summary"]["targets_failed"] = sum(
        row["status"] != "completed" for row in explicit_targets
    )
    if result["summary"]["targets_failed"]:
        result["summary"]["assessment_status"] = "inventory_incomplete"
    result["limitations"].append(
        "SSH and WSL target probes inspect command/configuration presence only; they do not read configuration contents or credentials."
    )
    if assets:
        result["asset_inventory"] = inventory_assets(
            target,
            max_files=max_files,
            hash_contents=hash_assets,
            max_hash_bytes=max_asset_hash_bytes,
        )
        result["privacy"]["security_asset_contents_read_locally"] = hash_assets
    if inspect_config:
        if "asset_inventory" not in result:
            raise click.ClickException("--inspect-config requires asset inventory; remove --no-assets")
        result["configuration_inspection"] = inspect_inventory(
            target, result["asset_inventory"], max_bytes=max_config_bytes
        )
        result["privacy"]["mode"] = "metadata_plus_redacted_structure"
        result["privacy"]["configuration_contents_read_locally"] = True
    if baseline:
        try:
            result["drift"] = compare_discovery(result, load_baseline(baseline))
        except (OSError, ValueError) as exc:
            raise click.ClickException(str(exc)) from exc
    if assess:
        result["posture"] = assess_posture(result)
    if policy:
        try:
            result["policy_decision"] = evaluate_policy(result, load_policy(policy))
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
    seal_inventory(result)
    if card_format and card_output:
        card_output.parent.mkdir(parents=True, exist_ok=True)
        card = (
            render_environment_html(result)
            if card_format == "html"
            else render_environment_markdown(result)
        )
        card_output.write_text(card, encoding="utf-8")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if fmt == "json":
        click.echo(json.dumps(result, indent=2))
        if enforce_policy:
            raise SystemExit(result["policy_decision"]["exit_code"])
        return
    summary = result["summary"]
    click.echo("AI SAFE2 Environment Doctor")
    click.echo(f"Scope: {result['scope']['root']}")
    click.echo(f"Harnesses detected: {summary['harnesses_detected']}")
    for harness in result["harnesses"]:
        sources = len(harness["commands"]) + len(harness["evidence"])
        click.echo(f"  - {harness['id']}: {harness['confidence']} confidence ({sources} indicators)")
    click.echo(f"Execution environments: {summary['execution_environments']}")
    for environment in result["environments"]:
        if environment["id"] == "wsl":
            names = ", ".join(environment["distributions"]) or "none inventoried"
            click.echo(f"  - WSL: {environment['status']} ({names})")
        else:
            click.echo(f"  - host: {environment['system']} {environment['release']}")
    click.echo(f"Shells detected: {summary['shells_detected']}")
    if "asset_inventory" in result:
        asset_inventory = result["asset_inventory"]
        click.echo(
            f"Security-relevant project assets: {len(asset_inventory['assets'])} "
            f"(visited {asset_inventory['files_visited']} files)"
        )
        for asset_type, count in sorted(asset_inventory["counts"].items()):
            click.echo(f"  - {asset_type}: {count}")
        if asset_inventory["truncated"]:
            click.echo("  - WARNING: asset traversal limit reached; inventory is incomplete")
    if "configuration_inspection" in result:
        config_summary = result["configuration_inspection"]["summary"]
        click.echo(
            f"Configuration inspection: {config_summary['completed']} completed, "
            f"{config_summary['incomplete']} incomplete, {config_summary['mcp_servers']} MCP servers"
        )
    if "drift" in result:
        drift = result["drift"]
        click.echo(f"Baseline drift: {drift['changes']} changes")
        for category, count in sorted(drift["counts"].items()):
            click.echo(f"  - {category}: {count}")
    if result["targets"]:
        click.echo(
            f"Explicit targets: {summary['targets_completed']} completed, "
            f"{summary['targets_failed']} incomplete"
        )
        for target_result in result["targets"]:
            click.echo(
                f"  - {target_result['id']}: {target_result['status']} "
                f"({len(target_result['harnesses'])} harnesses)"
            )
    privacy_note = (
        "configuration files were read locally for opted-in structural inspection; "
        "no raw contents or secret values were emitted or retained"
        if inspect_config
        else "configuration contents and secret values were not read"
    )
    click.echo(f"Assessment status: {summary['assessment_status']}; {privacy_note}.")
    if "posture" in result:
        posture = result["posture"]
        click.echo(f"Posture disposition: {posture['disposition']}")
        for finding in posture["findings"]:
            click.echo(f"  - [{finding['severity'].upper()}] {finding['id']}: {finding['title']}")
            click.echo(f"    Next: {finding['recommendation']}")
    if "policy_decision" in result:
        decision = result["policy_decision"]
        click.echo(
            f"Policy decision: {decision['disposition']} "
            f"({len(decision['violations'])} violations, "
            f"{len(decision['unmet_prerequisites'])} unmet prerequisites)"
        )
    integrity = result["integrity"]
    click.echo(
        f"Evidence integrity: sha256:{integrity['digest']} "
        f"({integrity['authenticity']})"
    )
    if output:
        click.echo(f"Evidence bundle: {output}")
    if card_output:
        click.echo(f"Environment Decision Card: {card_output}")
    if enforce_policy:
        raise SystemExit(result["policy_decision"]["exit_code"])
