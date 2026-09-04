"""
AI SAFE2 v3.1 Scanner - CP.5.MCP profile rules.

These rules target the agent-to-tool enforcement plane for MCP deployments.
They intentionally do not require server/discover to exist. MCP 2026-07-28
makes discovery optional, so presence is not a conformance condition.

MCP-19 remains advisory in the scanner until a deployment-specific resource
or audience validation path can be proven from code and configuration.
"""

from __future__ import annotations

import re

from .base import Rule

_CODE_EXTS = (".py", ".js", ".ts", ".tsx", ".mjs", ".cjs")
_CONFIG_EXTS = (".json", ".yaml", ".yml", ".toml", ".env")
_MCP_MARKERS = (
    "modelcontextprotocol",
    "from mcp.",
    "import mcp.",
    "@mcp.",
    "mcpservers",
    "stdioServerParameters".lower(),
    "tools/list",
    "tools/call",
    "mcp-method",
    "mcp-name",
)


def _is_mcp_target(content: str, filepath: str) -> bool:
    lower_path = filepath.replace("\\", "/").lower()
    if lower_path.endswith("scanner/rules/mcp_profile.py"):
        return False
    if "/tests/" in lower_path or "/test/" in lower_path:
        return False
    lower = content.lower()
    return any(marker in lower for marker in _MCP_MARKERS)


def _first_mcp_line(lines: list[str]) -> tuple[int, str]:
    for index, line in enumerate(lines, start=1):
        if any(marker in line.lower() for marker in _MCP_MARKERS):
            return index, line.strip()[:180]
    return 1, "MCP implementation detected"


def _check_dynamic_command(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    findings: list[tuple[int, str]] = []
    dynamic_patterns = (
        r"subprocess\.(run|popen|call|check_output|check_call)\s*\([^\n]*(input|request|argument|param|tool)",
        r"os\.system\s*\([^\n]*(input|request|argument|param|tool)",
        r"shell\s*=\s*true",
        r"exec\s*\(",
        r"eval\s*\(",
    )
    for index, line in enumerate(lines, start=1):
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in dynamic_patterns):
            findings.append((index, line.strip()[:180]))
    return findings


def _check_return_sanitization(
    content: str, lines: list[str], filepath: str
) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    has_tool_result = any(
        token in lower for token in ("tool_result", "toolresult", "call_tool", "tools/call")
    )
    has_sanitizer = any(
        token in lower
        for token in (
            "sanitize",
            "response_scanner",
            "scan_output",
            "prompt_injection",
            "untrusted_content",
        )
    )
    if has_tool_result and not has_sanitizer:
        return [_first_mcp_line(lines)]
    return []


def _check_server_integrity(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    launches_server = any(
        token in lower
        for token in (
            "stdioserverparameters",
            "mcpservers",
            "create_subprocess",
            "subprocess.popen",
        )
    )
    integrity = any(
        token in lower
        for token in (
            "sha256",
            "checksum",
            "signature",
            "allowlist",
            "manifest",
            "verify_integrity",
        )
    )
    if launches_server and not integrity:
        return [_first_mcp_line(lines)]
    return []


def _check_audit(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    handles_calls = any(
        token in lower for token in ("tools/call", "call_tool", "tool_call", "@mcp.tool")
    )
    audit = any(
        token in lower
        for token in (
            "audit",
            "opentelemetry",
            "otel",
            "receipt",
            "nor",
            "trace_id",
            "execution_trace",
        )
    )
    if handles_calls and not audit:
        return [_first_mcp_line(lines)]
    return []


def _check_input_validation(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    handles_calls = any(
        token in lower for token in ("tools/call", "call_tool", "@mcp.tool", "arguments")
    )
    validation = any(
        token in lower
        for token in (
            "jsonschema",
            "pydantic",
            "model_validate",
            "validate_input",
            "schema.validate",
            "zod",
        )
    )
    if handles_calls and not validation:
        return [_first_mcp_line(lines)]
    return []


def _check_trust_establishment(
    content: str, lines: list[str], filepath: str
) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    if "wrap-stdio" in lower and "streamable-http" not in lower:
        return []
    networked = any(
        token in lower for token in ("streamable-http", "sse", "authorization", "bearer ", "oauth")
    )
    trust = any(
        token in lower
        for token in (
            "principal",
            "authenticate",
            "authorization",
            "capability_grant",
            "policy_context",
            "verify_token",
        )
    )
    if networked and not trust:
        return [_first_mcp_line(lines)]
    return []


def _check_economic_ceiling(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    handles_calls = any(token in lower for token in ("tools/call", "call_tool", "@mcp.tool"))
    ceiling = any(
        token in lower
        for token in (
            "rate_limit",
            "ratelimit",
            "quota",
            "budget",
            "cost_ceiling",
            "token_limit",
            "max_calls",
        )
    )
    if handles_calls and not ceiling:
        return [_first_mcp_line(lines)]
    return []


def _check_delegation_lineage(
    content: str, lines: list[str], filepath: str
) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    multi_agent = any(
        token in lower
        for token in (
            "delegate",
            "subagent",
            "sub-agent",
            "spawn_agent",
            "agent_id",
            "parent_did",
            "chain_id",
        )
    )
    lineage = any(
        token in lower
        for token in (
            "delegation_chain",
            "lineage_token",
            "parent_did",
            "chain_id",
            "capability_grant_id",
        )
    )
    if multi_agent and not lineage:
        return [_first_mcp_line(lines)]
    return []


def _check_catalog_provenance(
    content: str, lines: list[str], filepath: str
) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    uses_catalog = any(
        token in lower for token in ("tools/list", "list_tools", "resources/list", "prompts/list")
    )
    revalidates = any(
        token in lower
        for token in (
            "catalog_hash",
            "schema_hash",
            "provenance",
            "revalidate",
            "cache_ttl",
            "baseline_hash",
        )
    )
    if uses_catalog and not revalidates:
        return [_first_mcp_line(lines)]
    return []


def _check_state_handle_binding(
    content: str, lines: list[str], filepath: str
) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    findings: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        lower = line.lower()
        if "mcp-session-id" in lower and any(
            token in lower
            for token in ("identity", "principal", "authenticate", "authorize", "user_id", "owner")
        ):
            findings.append((index, line.strip()[:180]))
    return findings


def _check_protocol_integrity(
    content: str, lines: list[str], filepath: str
) -> list[tuple[int, str]]:
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    uses_assertion_headers = "mcp-method" in lower or "mcp-name" in lower
    verifies_match = any(
        token in lower
        for token in (
            "header_body",
            "assertion_integrity",
            "method_matches",
            "name_matches",
            "compare_header",
        )
    )
    uses_mrtr = "mrtr" in lower or "model-mediated" in lower
    replay = any(token in lower for token in ("nonce", "request_id", "replay", "response_hash"))
    if uses_assertion_headers and not verifies_match:
        return [_first_mcp_line(lines)]
    if uses_mrtr and not replay:
        return [_first_mcp_line(lines)]
    return []


def _check_mcp19_auth_chain(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """Advisory check for intended-resource/audience and SSRF validation."""
    if not _is_mcp_target(content, filepath):
        return []
    lower = content.lower()
    auth_surface = any(
        token in lower
        for token in ("oauth", "authorization", "bearer", "jwt", "jwks", "protected resource")
    )
    if not auth_surface:
        return []
    resource_binding = any(
        token in lower
        for token in (
            "audience",
            '"aud"',
            "['aud']",
            "resource_indicator",
            "intended_resource",
            "mcp_auth_audience",
        )
    )
    ssrf = any(
        token in lower
        for token in (
            "ssrf",
            "allowed_hosts",
            "allowlisted_host",
            "url_allowlist",
            "validate_redirect",
            "validate_resource_url",
        )
    )
    if not resource_binding or not ssrf:
        return [_first_mcp_line(lines)]
    return []


MCP_PROFILE_RULES: list[Rule] = [
    Rule(
        control_id="MCP-1",
        severity="CRITICAL",
        description="MCP implementation contains dynamic command execution patterns that may cross the tool trust boundary.",
        remediation="Use statically defined server commands and strict allowlists. Never place untrusted tool or request data into shell or subprocess command construction.",
        check_fn=_check_dynamic_command,
        file_exts=_CODE_EXTS,
    ),
    Rule(
        control_id="MCP-2",
        severity="HIGH",
        description="MCP tool results appear to enter application/model context without an explicit untrusted-content sanitization step.",
        remediation="Treat all MCP return data as untrusted. Scan or sanitize returned content before placing it into model context or privileged application flows.",
        check_fn=_check_return_sanitization,
        file_exts=_CODE_EXTS,
    ),
    Rule(
        control_id="MCP-4",
        severity="HIGH",
        description="MCP server launch or configuration detected without visible server/binary provenance or integrity verification.",
        remediation="Bind approved MCP servers to a manifest, checksum, signature, endpoint identity, or equivalent provenance baseline and fail closed on mismatch.",
        check_fn=_check_server_integrity,
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
    ),
    Rule(
        control_id="MCP-5",
        severity="HIGH",
        description="MCP tool invocation path detected without attributable audit or trace evidence.",
        remediation="Emit immutable or externally protected invocation evidence with principal, tool, request, outcome, policy decision, and timestamps.",
        check_fn=_check_audit,
        file_exts=_CODE_EXTS,
    ),
    Rule(
        control_id="MCP-6",
        severity="HIGH",
        description="MCP tool invocation path detected without explicit argument/schema validation.",
        remediation="Validate tool inputs against the authorized schema and policy before dispatch. Reject unknown or malformed fields.",
        check_fn=_check_input_validation,
        file_exts=_CODE_EXTS,
    ),
    Rule(
        control_id="MCP-7",
        severity="HIGH",
        description="Networked MCP surface detected without clear verified-principal and trust-establishment logic.",
        remediation="Establish a verified principal, capability grant, and policy context before protected tool use. Do not use a transport session identifier as identity.",
        check_fn=_check_trust_establishment,
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
    ),
    Rule(
        control_id="MCP-8",
        severity="MEDIUM",
        description="MCP tool invocation path detected without visible quota, rate, or economic ceiling enforcement.",
        remediation="Account consumption to the verified principal and fail closed when authorized call, token, cost, or time ceilings are reached.",
        check_fn=_check_economic_ceiling,
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
    ),
    Rule(
        control_id="MCP-9",
        severity="CRITICAL",
        description="Potential secret material is passed through an MCP argument, log, or configuration boundary.",
        remediation="Keep secrets outside model context, tool arguments, and ordinary logs. Use a credential broker or secret reference and redact evidence outputs.",
        pattern=r"(?i)(mcp|tool).{0,80}(api[_-]?key|secret|password|private[_-]?key|bearer\s+[A-Za-z0-9._-]{16,})",
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
        skip_comments=False,
    ),
    Rule(
        control_id="MCP-10",
        severity="HIGH",
        description="Multi-agent MCP use detected without visible originating delegation lineage.",
        remediation="Carry the originating principal and delegation chain through every agent-to-tool action, including capability-grant and lineage identifiers where applicable.",
        check_fn=_check_delegation_lineage,
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
    ),
    Rule(
        control_id="MCP-18",
        severity="MEDIUM",
        description="MCP catalog use detected without visible provenance baseline, cache TTL, or revalidation logic.",
        remediation="Hash or otherwise identify authorized tool/resource/prompt catalogs, policy-bound cache lifetimes, and revalidate when trust context or catalog content changes.",
        check_fn=_check_catalog_provenance,
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
    ),
    Rule(
        control_id="MCP-16",
        severity="CRITICAL",
        description="Legacy Mcp-Session-Id appears to be used as identity, ownership, authentication, or authorization state.",
        remediation="Treat legacy Mcp-Session-Id only as a principal-scoped state handle. Bind authorization to a verified principal and policy context, not possession of the handle.",
        check_fn=_check_state_handle_binding,
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
    ),
    Rule(
        control_id="MCP-19",
        severity="INFO",
        description="MCP authorization surface may lack complete intended-resource/audience and SSRF boundary validation. This scanner finding is advisory.",
        remediation="For protected MCP requests, validate issuer and intended resource/audience, bind redirects and authorization metadata, and restrict resource/redirect URLs against SSRF. Opaque bearer tokens do not prove audience validation by themselves.",
        check_fn=_check_mcp19_auth_chain,
        file_exts=_CODE_EXTS + _CONFIG_EXTS,
    ),
]

# Public alias used by scanner/rules/__init__.py.
MCP_RULES = MCP_PROFILE_RULES
