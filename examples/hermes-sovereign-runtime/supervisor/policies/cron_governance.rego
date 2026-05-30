package hsr.cron_governance

# =============================================================================
# Cron Automation Governance Policy — Hermes Sovereign Runtime
# AI SAFE² v3.0 | Cyber Strategy Institute
#
# All scheduled (cron) automation must pass this policy before execution.
# Unattended AI automation is the highest-risk operational category.
# This policy enforces: approval, scope, network isolation, and time limits.
# =============================================================================

import future.keywords.if
import future.keywords.in

default allow_schedule := false
default allow_execute := false
default requires_renewal := false

# ---------------------------------------------------------------------------
# SCHEDULING — Can this cron job be created?
# ---------------------------------------------------------------------------

allow_schedule if {
    input.request_type == "schedule"
    has_operator_approval
    valid_tool_scope
    not exceeds_runtime_limit
    not requires_network_blocked_tool
}

has_operator_approval if {
    input.approval.present == true
    input.approval.operator_id != ""
    # Approval must be less than 30 days old
    input.approval.timestamp > time.now_ns() - (30 * 24 * 60 * 60 * 1000000000)
}

valid_tool_scope if {
    allowed_cron_tools := {"read_file", "web_fetch", "memory_search", "list_directory", "memory_write"}
    count({tool | tool := input.tools[_]; not tool in allowed_cron_tools}) == 0
}

exceeds_runtime_limit if {
    input.max_runtime_seconds > 300
}

requires_network_blocked_tool if {
    network_blocked := {"terminal", "spawn_subagent", "install_plugin", "pip_install", "git_push"}
    some tool in input.tools
    tool in network_blocked
}

# ---------------------------------------------------------------------------
# EXECUTION — Can this scheduled job run right now?
# ---------------------------------------------------------------------------

allow_execute if {
    input.request_type == "execute"
    approval_still_valid
    not kill_switch_active
    within_allowed_window
    not anomaly_score_exceeded
}

approval_still_valid if {
    input.approval.timestamp > time.now_ns() - (30 * 24 * 60 * 60 * 1000000000)
}

kill_switch_active if {
    input.context.kill_switch == true
}

within_allowed_window if {
    # Allow execution during configured windows
    # Default: all hours allowed (operators customize per deployment)
    true
}

anomaly_score_exceeded if {
    input.context.anomaly_score > 0.85
}

# ---------------------------------------------------------------------------
# RENEWAL REQUIRED
# ---------------------------------------------------------------------------

requires_renewal if {
    input.request_type == "execute"
    age_days := (time.now_ns() - input.approval.timestamp) / (24 * 60 * 60 * 1000000000)
    age_days > 25   # Warn 5 days before expiry
}

# ---------------------------------------------------------------------------
# BLOCKED CRON PATTERNS
# These patterns are never allowed in cron context regardless of approval
# ---------------------------------------------------------------------------

blocked_cron_pattern if {
    input.tools[_] == "terminal"
}

blocked_cron_pattern if {
    input.tools[_] == "spawn_subagent"
}

blocked_cron_pattern if {
    input.tools[_] == "install_plugin"
}

# Final deny if blocked pattern detected
allow_schedule := false if {
    blocked_cron_pattern
}

allow_execute := false if {
    blocked_cron_pattern
}

# ---------------------------------------------------------------------------
# AUDIT METADATA
# ---------------------------------------------------------------------------

policy_version := "1.0.0"
framework := "AI SAFE² v3.0"
pillar := "P3-Fail-Safe-Recovery"
