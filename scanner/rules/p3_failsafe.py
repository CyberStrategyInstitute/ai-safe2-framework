"""
AI SAFE2 v3.0 Scanner — Pillar 3: Fail-Safe & Recovery Rules
Covers: P3.T5.x (Fail-Safe), P3.T6.x (Recovery), F3.2-F3.5 (v3.0 new controls)
"""
from __future__ import annotations

import re
from .base import Rule


def _check_recursion_without_limit(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    F3.2 — Agent Recursion Limit Governor
    Detect agent/tool-calling loops without a depth or recursion limit.
    The limit must be at the infrastructure/gateway layer, not just in the system prompt.
    """
    findings = []
    # Patterns that suggest a recursive or looping tool-calling structure
    recursive_patterns = [
        r"while\s+True\s*:",
        r"def\s+\w+.*:\s*\n.*\1\s*\(",   # simple recursion signature
        r"for\s+step\s+in\s+range\(",
        r"\.run_until_complete\(",
        r"agent\.run\(",
        r"executor\.run\(",
        r"chain\.invoke\(",
        r"tool_call\s*=",
    ]
    limit_words = {
        "max_depth", "max_iterations", "recursion_limit", "depth_limit",
        "max_steps", "iteration_limit", "recursion_depth", "tool_call_limit",
        "f3_2", "recursion_governor", "sys.setrecursionlimit"
    }

    for i, line in enumerate(lines):
        for pat in recursive_patterns:
            if re.search(pat, line, re.IGNORECASE):
                # Check ±10 lines for a limit definition
                start = max(0, i - 5)
                end = min(len(lines), i + 10)
                context = " ".join(lines[start:end]).lower()
                if not any(w in context for w in limit_words):
                    # Extra check: is there a while True without break?
                    if "while true" in line.lower():
                        window = lines[i:min(i + 20, len(lines))]
                        window_text = " ".join(window).lower()
                        if "break" not in window_text and "return" not in window_text:
                            findings.append((
                                i + 1,
                                f"Infinite loop without break/return or recursion limit: {line.strip()[:60]}"
                            ))
                    else:
                        findings.append((
                            i + 1,
                            f"Tool-calling loop without depth limit: {line.strip()[:60]}"
                        ))
                    break
    return findings


def _check_missing_error_handling(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    P3.T5.4 — Error Handling
    Detect LLM API calls not wrapped in exception handlers.
    """
    findings = []
    llm_call_patterns = [
        r"\.chat\.completions\.create\(", r"client\.messages\.create\(",
        r"openai\.", r"anthropic\.", r"\.invoke\(", r"agent\.run\(",
    ]
    try_words = {"try", "except", "catch", "finally", "error", "fallback",
                 "retry", "timeout", "on_error"}

    for i, line in enumerate(lines):
        for pat in llm_call_patterns:
            if re.search(pat, line, re.IGNORECASE):
                # Check ±8 lines for try/except wrapper
                start = max(0, i - 5)
                end = min(len(lines), i + 5)
                context = " ".join(lines[start:end]).lower()
                if not any(w in context for w in try_words):
                    findings.append((
                        i + 1,
                        f"LLM API call without exception handling — no fallback: {line.strip()[:50]}"
                    ))
                break
    return findings


P3_RULES: list[Rule] = [

    # ── P3.T5.x Fail-Safe ─────────────────────────────────────────────────────

    Rule(
        control_id="P3.T5.1",
        severity="MEDIUM",
        description="Potential infinite loop — while True without evident break, return, or recursion limit.",
        remediation="Apply P3.T5.1: add a circuit breaker. Define maximum iterations or "
                    "implement F3.2 Recursion Limit Governor at the API gateway layer.",
        check_fn=_check_recursion_without_limit,
        file_exts=(".py", ".js", ".ts"),
    ),
    Rule(
        control_id="P3.T5.4",
        severity="HIGH",
        description="LLM API call without exception handling — no fallback or timeout defined.",
        remediation="Wrap all LLM API calls in try/except with a defined fallback. "
                    "Set timeouts. Implement exponential backoff for retries.",
        check_fn=_check_missing_error_handling,
        file_exts=(".py", ".js", ".ts"),
    ),
    Rule(
        control_id="P3.T5.5",
        severity="MEDIUM",
        description="No rate limiting or token budget enforcement found in agent code.",
        remediation="Apply P3.T5.5: implement per-agent token quotas and API rate limits. "
                    "Use F3.2 recursion governor to prevent runaway tool-call loops.",
        pattern=r"(openai\.|anthropic\.|\.invoke\(|agent\.run)",
        file_exts=(".py", ".js", ".ts"),
        # Note: this is a presence check — real analysis done in scanner structural pass
    ),
    Rule(
        control_id="P3.T5.7",
        severity="HIGH",
        description="No kill switch or emergency shutdown mechanism detected in agent configuration.",
        remediation="Implement P3.T5.7: define a kill switch endpoint or process signal handler. "
                    "For ACT-3/4 agents, this is a deployment blocker per CP.8.",
        pattern=r"(?i)(kill_switch|emergency_stop|shutdown|halt_agent|revoke_agent)",
        file_exts=(".py", ".js", ".ts", ".yaml"),
        # Also absence — noted in structural check
    ),
    Rule(
        control_id="P3.T5.8",
        severity="HIGH",
        description="Agent spawning without blast radius containment — "
                    "failures can propagate to all downstream agents.",
        remediation="Apply P3.T5.8 and F3.5: define containment zones for agent failures. "
                    "Implement cascade containment so one failing agent cannot "
                    "corrupt downstream agents in the pipeline.",
        pattern=r"(subprocess\.Popen|multiprocessing\.Process|threading\.Thread|asyncio\.create_task|spawn_agent|create_agent)",
        file_exts=(".py",),
    ),

    # ── F3.2-F3.5 New v3.0 Controls ──────────────────────────────────────────

    # F3.2 — Recursion Limit Governor (structural check above + pattern)
    Rule(
        control_id="F3.2",
        severity="CRITICAL",
        description="Agent tool-calling or orchestration loop without recursion depth limit — "
                    "budget burn risk. Limit must be at the gateway layer, not in the system prompt.",
        remediation="Apply F3.2: enforce a hard cap on tool-calling depth at the API gateway "
                    "layer. Default maximum depth: 4. When exceeded, gateway returns error; "
                    "agent stops. Do not rely on system prompt instructions for this limit.",
        check_fn=_check_recursion_without_limit,
        file_exts=(".py", ".js", ".ts"),
    ),

    # F3.5 — Multi-Agent Cascade Containment
    Rule(
        control_id="F3.5",
        severity="HIGH",
        description="Multi-agent pipeline without cascade containment — "
                    "one agent failure may propagate silently to all downstream stages.",
        remediation="Apply F3.5: implement isolation boundaries between pipeline stages. "
                    "Failed agents must return clean error signals — not malformed data — "
                    "to downstream agents. Use circuit breaker pattern at each stage boundary.",
        pattern=r"(pipe|pipeline|chain|sequence|workflow|orchestrat)",
        file_exts=(".py", ".js", ".ts", ".yaml"),
    ),

    # Recovery checks
    Rule(
        control_id="P3.T6.6",
        severity="LOW",
        description="No RTO/RPO definitions found in configuration — "
                    "recovery objectives not formally documented.",
        remediation="Define Recovery Time Objective and Recovery Point Objective for AI components. "
                    "Include in disaster recovery plan per P3.T6.4.",
        pattern=r"(?i)(rto|rpo|recovery_time|recovery_point)",
        file_exts=(".yaml", ".yml", ".json", ".toml"),
    ),
]
