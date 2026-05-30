package hsr.tool_approval

# =============================================================================
# Tool Approval Policy — Hermes Sovereign Runtime
# AI SAFE² v3.0 | Cyber Strategy Institute
#
# Evaluated by Ishi supervisor agent via OPA sidecar.
# Input: { tool, parameters, agent_id, alignment_score, context }
# Output: { allow, deny, reason, escalate_to_human }
# =============================================================================

import future.keywords.if
import future.keywords.in

# ---------------------------------------------------------------------------
# Default deny — explicit allow required
# ---------------------------------------------------------------------------
default allow := false
default deny := true
default escalate_to_human := false

# ---------------------------------------------------------------------------
# UNCONDITIONAL DENIES — No operator override, no alignment score exception
# ---------------------------------------------------------------------------

deny if {
    input.tool == "terminal"
    input.parameters.yolo == true
}

deny if {
    input.tool == "write_file"
    is_credential_path(input.parameters.path)
}

deny if {
    input.tool == "read_file"
    is_system_critical_path(input.parameters.path)
    not input.context.vault_token_present
}

deny if {
    input.tool == "install_plugin"
    not input.parameters.signature_verified == true
}

deny if {
    input.tool == "spawn_subagent"
    input.parameters.tool_inheritance == "full"
}

deny if {
    # Block community skills without provenance verification
    input.tool == "execute_skill"
    input.parameters.source == "community"
    not input.parameters.provenance_verified == true
}

deny if {
    # Block any skill not in the sovereign registry
    input.tool == "execute_skill"
    not input.parameters.skill_id in data.sovereign_registry.approved_skills
}

# ---------------------------------------------------------------------------
# ALIGNMENT-GATED APPROVALS
# Red band: deny all tool execution requiring oversight
# ---------------------------------------------------------------------------

deny if {
    input.alignment_score.E < 4.0
    requires_oversight(input.tool)
}

deny if {
    input.alignment_score.I < 3.5
    requires_oversight(input.tool)
}

# ---------------------------------------------------------------------------
# HUMAN ESCALATION — Route to operator review
# ---------------------------------------------------------------------------

escalate_to_human if {
    input.alignment_score.E >= 4.0
    input.alignment_score.E < 6.0
    high_risk_tool(input.tool)
}

escalate_to_human if {
    input.tool == "terminal"
    not input.context.cron_context == true
}

escalate_to_human if {
    input.tool == "send_message"
    count(input.parameters.content) > 10000
}

escalate_to_human if {
    input.tool == "cron_create"
}

escalate_to_human if {
    input.tool == "spawn_subagent"
}

# ---------------------------------------------------------------------------
# ALLOWS — After all deny checks pass
# ---------------------------------------------------------------------------

allow if {
    not deny
    not escalate_to_human
    safe_tool(input.tool)
}

allow if {
    not deny
    escalate_to_human
    input.context.operator_approved == true
    input.context.approval_timestamp > time.now_ns() - (300 * 1000000000)  # 5-min window
}

# ---------------------------------------------------------------------------
# HELPER RULES
# ---------------------------------------------------------------------------

is_credential_path(path) if {
    credential_paths := [
        "~/.ssh/", "/etc/ssl/", "~/.aws/", "~/.gcp/", "~/.azure/",
        "~/.kube/", "/var/run/secrets/", "~/.gnupg/"
    ]
    some cp in credential_paths
    startswith(path, cp)
}

is_system_critical_path(path) if {
    critical_paths := ["/etc/", "/var/run/", "/proc/", "/sys/", "/boot/"]
    some cp in critical_paths
    startswith(path, cp)
}

high_risk_tool(tool) if {
    high_risk := {"terminal", "write_file", "install_plugin", "spawn_subagent", "cron_create", "git_push", "pip_install"}
    tool in high_risk
}

requires_oversight(tool) if {
    oversight_tools := {"terminal", "write_file", "install_plugin", "spawn_subagent",
                        "send_message", "cron_create", "execute_skill", "git_push"}
    tool in oversight_tools
}

safe_tool(tool) if {
    safe := {"read_file", "web_search", "memory_search", "list_directory",
             "web_fetch", "memory_write", "skill_list"}
    tool in safe
}

# ---------------------------------------------------------------------------
# POLICY METADATA (for audit trail)
# ---------------------------------------------------------------------------

policy_version := "1.0.0"
policy_author := "Cyber Strategy Institute"
framework := "AI SAFE² v3.0"
