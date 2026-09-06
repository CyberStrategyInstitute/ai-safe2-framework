"""Evidence-bounded posture findings derived from discovery results."""

from __future__ import annotations

from typing import Any

PROJECT_POLICY = {
    "codex": "AGENTS.md",
    "claude-code": "CLAUDE.md",
    "antigravity": ".antigravity",
    "hermes": ".hermes",
    "openclaw": ".openclaw",
    "grok": ".grok",
}


def _finding(
    finding_id: str,
    severity: str,
    category: str,
    title: str,
    facts: list[str],
    assumptions: list[str],
    recommendation: str,
    candidate_controls: list[str],
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "category": category,
        "title": title,
        "facts": facts,
        "assumptions": assumptions,
        "recommendation": recommendation,
        "candidate_controls": candidate_controls,
        "verification": "derived_from_discovery",
    }


def assess_posture(discovery: dict[str, Any]) -> dict[str, Any]:
    """Produce scoped findings without treating absence as proof of insecurity."""
    findings: list[dict[str, Any]] = []
    harnesses = discovery.get("harnesses", [])
    targets = discovery.get("targets", [])
    asset_inventory = discovery.get("asset_inventory", {})
    asset_counts = asset_inventory.get("counts", {})
    config_inspection = discovery.get("configuration_inspection", {})
    config_summary = config_inspection.get("summary", {})
    drift = discovery.get("drift", {})
    findings.extend(drift.get("findings", []))

    if config_summary.get("incomplete", 0):
        findings.append(
            _finding(
                "CONFIG-INSPECTION-INCOMPLETE",
                "high",
                "coverage_gap",
                "One or more opted-in configuration inspections were incomplete",
                [f"Incomplete configuration inspections: {config_summary['incomplete']}."],
                ["Unparsed or skipped configuration may contain security-relevant settings not represented in this posture."],
                "Resolve format, access, or size-limit failures and rerun before relying on configuration coverage.",
                ["P2", "CP.1"],
            )
        )

    if config_summary.get("secret_like_keys", 0):
        findings.append(
            _finding(
                "CONFIG-SECRET-HANDLING-REVIEW",
                "medium",
                "credential_governance",
                "Configuration contains keys commonly associated with secrets or credentials",
                [f"Structural inspection found {config_summary['secret_like_keys']} secret-like key names; no values were emitted."],
                ["A matching key may contain an environment-variable reference or placeholder rather than a stored secret."],
                "Verify that active credentials come from an approved secret provider, are scoped and short-lived, and are not committed in plaintext.",
                ["P1", "P2", "CP.1"],
            )
        )

    for config_file in config_inspection.get("files", []):
        policy = config_file.get("runtime_policy", {})
        sandbox = str(policy.get("sandbox_mode", "")).lower()
        approval = str(policy.get("approval_policy", "")).lower()
        permissive_sandbox = sandbox in {"danger-full-access", "bypass", "disabled", "none"}
        permissive_approval = approval in {"never", "bypass", "bypasspermissions", "dontask"}
        if permissive_sandbox or permissive_approval:
            severity = "high" if permissive_sandbox and permissive_approval else "medium"
            findings.append(
                _finding(
                    f"PERMISSIVE-RUNTIME-{len(findings) + 1}",
                    severity,
                    "runtime_policy",
                    "Harness configuration declares a permissive sandbox or approval mode",
                    [
                        f"Redacted structural inspection observed sandbox={sandbox or 'unspecified'} and approval={approval or 'unspecified'} in {config_file.get('path', 'a configuration file')}."
                    ],
                    ["The setting may be intentionally constrained by controls outside this file or used only in an isolated environment."],
                    "Confirm the effective runtime boundary, external compensating controls, authorized use case, owner, and expiration before unattended execution.",
                    ["P1", "P3", "CP.1"],
                )
            )

    if asset_inventory.get("truncated"):
        findings.append(
            _finding(
                "ASSET-INVENTORY-TRUNCATED",
                "high",
                "coverage_gap",
                "Project asset inventory reached its traversal limit",
                [
                    f"The collector stopped after visiting {asset_inventory.get('files_visited', 'unknown')} files."
                ],
                ["Security-relevant assets beyond the traversal boundary may be absent from the inventory."],
                "Rerun with a larger --max-files limit or assess narrower project roots separately.",
                ["P2"],
            )
        )

    if asset_counts.get("persistent_agent_state", 0):
        findings.append(
            _finding(
                "PERSISTENT-STATE-REVIEW",
                "medium",
                "memory_governance",
                "Persistent agent-state files require provenance and write-governance review",
                [f"Found {asset_counts['persistent_agent_state']} persistent agent-state file indicators."],
                ["Filename-based discovery does not establish whether the files are active or writable by an agent."],
                "Confirm ownership, write authority, provenance, review, quarantine, and rollback behavior for durable agent state.",
                ["P1", "P2", "P3"],
            )
        )

    if asset_counts.get("scheduled_agent_operation", 0):
        findings.append(
            _finding(
                "SCHEDULED-AUTONOMY-REVIEW",
                "medium",
                "scheduled_operations",
                "Scheduled or heartbeat agent-operation indicators require authority review",
                [f"Found {asset_counts['scheduled_agent_operation']} scheduled-operation file indicators."],
                ["Filename-based discovery does not establish whether a schedule is active or can cause external side effects."],
                "Inventory triggers, frequency, owner, credentials, allowed side effects, approval gates, expiration, and kill-switch behavior.",
                ["P2", "P3", "P4", "CP.1"],
            )
        )

    if asset_counts.get("agent_skill", 0):
        findings.append(
            _finding(
                "SKILL-SUPPLY-CHAIN-REVIEW",
                "medium",
                "skill_governance",
                "Agent skills require trust, provenance, and promotion review",
                [f"Found {asset_counts['agent_skill']} agent skill manifests."],
                ["Presence does not establish that a skill is enabled, trusted, current, or unsafe."],
                "Run the AI SAFE2 skill gate for each active skill and record source, version, owner, permissions, and approval status.",
                ["P1", "P2", "CP.1"],
            )
        )

    if asset_counts.get("mcp_configuration", 0):
        findings.append(
            _finding(
                "MCP-INVENTORY-REVIEW",
                "medium",
                "mcp_governance",
                "MCP configuration candidates require server and capability inventory",
                [f"Found {asset_counts['mcp_configuration']} MCP configuration file indicators."],
                ["The metadata-only collector did not read server definitions, credentials, tools, or authorization settings."],
                "Use a consented MCP configuration collector, redact credentials, and baseline server/tool provenance before enabling access.",
                ["CP.5", "P2"],
            )
        )

    if asset_counts.get("infrastructure_as_code", 0) and harnesses:
        findings.append(
            _finding(
                "AGENT-IAC-BOUNDARY-REVIEW",
                "medium",
                "consequential_access",
                "Agent-enabled repository contains infrastructure-as-code assets",
                [f"Found {asset_counts['infrastructure_as_code']} infrastructure-as-code files and {len(harnesses)} local harness indicators."],
                ["Discovery does not prove that any harness may modify or deploy these assets."],
                "Confirm file, command, credential, plan, approval, and deployment boundaries before allowing agent-driven infrastructure changes.",
                ["P1", "P3", "CP.1"],
            )
        )

    for harness in harnesses:
        harness_id = harness["id"]
        project_evidence = [
            row for row in harness.get("evidence", []) if row.get("scope") == "project"
        ]
        if not project_evidence:
            marker = PROJECT_POLICY.get(harness_id, "a project policy")
            findings.append(
                _finding(
                    f"HARNESS-POLICY-{harness_id.upper()}",
                    "medium",
                    "policy_coverage",
                    f"No {harness_id} project policy was discovered at the assessed root",
                    [f"The {harness_id} harness has user configuration or an executable indicator."],
                    [
                        "The repository may intentionally rely on user-wide policy; discovery did not inspect policy contents.",
                        "A policy may exist under an unrecognized filename or outside the assessed root.",
                    ],
                    f"Confirm whether this repository uses {harness_id}; if it does, add or document the authoritative {marker} policy and verify its precedence.",
                    ["P2", "CP.1"],
                )
            )
        if not harness.get("commands"):
            findings.append(
                _finding(
                    f"HARNESS-PATH-{harness_id.upper()}",
                    "low",
                    "inventory_quality",
                    f"{harness_id} configuration was found but no executable was available on PATH",
                    ["Configuration metadata exists; command discovery returned no executable."],
                    ["The harness may be installed in WSL, a container, an IDE, or a non-PATH location."],
                    "Confirm the active installation location and record its version and owner before relying on this inventory.",
                    ["P2"],
                )
            )

    failed_targets = [row for row in targets if row.get("status") != "completed"]
    for target in failed_targets:
        findings.append(
            _finding(
                f"TARGET-INCOMPLETE-{len(findings) + 1}",
                "high",
                "coverage_gap",
                f"Explicit target {target.get('id', 'unknown')} was not inventoried",
                [f"Probe status: {target.get('status', 'unknown')}."],
                ["The target's harness, policy, tool, and evidence posture is unknown."],
                "Restore least-privilege read access or record a time-bounded exception; do not treat the target as clean.",
                ["P2", "CP.1"],
            )
        )

    completed_targets = [row for row in targets if row.get("status") == "completed"]
    total_harness_instances = len(harnesses) + sum(
        len(row.get("harnesses", [])) for row in completed_targets
    )
    if total_harness_instances > 1:
        findings.append(
            _finding(
                "MULTI-HARNESS-CONSISTENCY",
                "medium",
                "cross_harness_governance",
                "Multiple harness instances require a consistent governance baseline",
                [f"Discovery identified {total_harness_instances} harness instances across completed scopes."],
                ["Different harnesses may currently apply different permissions, instructions, and evidence behavior."],
                "Establish one authoritative AI SAFE2 policy baseline, then validate equivalent outcomes in each native harness configuration.",
                ["CP.1", "P2"],
            )
        )

    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    counts = {name: 0 for name in severity_order}
    for finding in findings:
        counts[finding["severity"]] += 1
    if failed_targets:
        disposition = "INCOMPLETE"
    elif any(severity_order[row["severity"]] >= 2 for row in findings):
        disposition = "REVIEW"
    else:
        disposition = "BASELINE"
    return {
        "schema_version": "safe2.environment-posture.v1",
        "scope": discovery.get("scope", {}),
        "disposition": disposition,
        "finding_counts": counts,
        "findings": findings,
        "coverage": {
            "local_inventory": True,
            "explicit_targets_requested": len(targets),
            "explicit_targets_completed": len(completed_targets),
            "explicit_targets_incomplete": len(failed_targets),
            "configuration_inspection_requested": bool(config_inspection),
            "configuration_candidates": config_summary.get("candidates", 0),
            "configuration_files_completed": config_summary.get("completed", 0),
            "configuration_contents_assessed": bool(config_summary.get("completed", 0)),
            "baseline_comparison": bool(drift),
            "baseline_changes": drift.get("changes", 0) if drift else None,
            "runtime_behavior_assessed": False,
            "cloud_control_planes_assessed": False,
        },
        "limitations": [
            "This posture is derived from metadata-only discovery.",
            "A missing policy indicator is a review prompt, not proof that governance is absent.",
            "Candidate control mappings require scope-specific validation before use as compliance evidence.",
            "No conformance, certification, or runtime-enforcement claim is made.",
        ],
    }
