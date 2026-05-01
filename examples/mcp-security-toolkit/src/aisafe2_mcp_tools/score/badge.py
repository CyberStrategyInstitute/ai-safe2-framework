"""
AI SAFE2 MCP Security Toolkit — Badge System
CP.5.MCP Score Badge for server operators scoring 70+.

Badge design philosophy:
  - Badge is earned, not self-issued
  - Anyone can re-scan to verify the score
  - The badge URL embeds the score + assessment timestamp
  - Builder adds .well-known/mcp-security.json to claim it
  - mcp-score verifies attestation during scan and adds bonus points

Badge eligibility: CP.5.MCP Score >= 70 (Acceptable or higher)

Badge URL format:
  https://img.shields.io/badge/AI%20SAFE2%20MCP-Score%3A{score}%2F100-{color}
  ?style=for-the-badge&logo=shield&logoColor=white

Or custom SVG (generated locally — no external dependency).

Embedding in README:
  [![AI SAFE2 MCP Score](badge_url)](https://cyberstrategyinstitute.com/ai-safe2/mcp-verify?url=YOUR_MCP_URL)

The link target is a CSI verification page that re-runs mcp-score live
against the server URL embedded in the query parameter.

.well-known/mcp-security.json specification:
  Builders add this file to their server root to claim attestation bonus
  and unlock additional scoring criteria for controls that cannot be
  verified remotely (source integrity, dynamic command check, audit logging).
"""
from __future__ import annotations

import json
from urllib.parse import quote

from aisafe2_mcp_tools.score.assessor import ScoreReport


# ── SVG Badge Generator ───────────────────────────────────────────────────────

def _badge_color(score: int) -> str:
    """Map score to badge color."""
    if score >= 90: return "#28a745"   # Green
    if score >= 70: return "#f6921e"   # CSI Orange (acceptable)
    if score >= 50: return "#ffc107"   # Yellow
    if score >= 30: return "#dc3545"   # Red
    return "#820f1a"                    # CSI Maroon (critical)


def generate_badge_svg(score: int, rating: str) -> str:
    """Generate a standalone SVG badge — no external dependency."""
    color = _badge_color(score)
    label = "AI SAFE2 MCP"
    value = f"Score: {score}/100"
    label_width = 120
    value_width = 110
    total_width = label_width + value_width

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {value}">
  <title>{label}: {value}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
    <text x="{label_width // 2 * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(label_width - 10) * 10}" lengthAdjust="spacing">{label}</text>
    <text x="{label_width // 2 * 10}" y="140" transform="scale(.1)" textLength="{(label_width - 10) * 10}" lengthAdjust="spacing">{label}</text>
    <text x="{(label_width + value_width // 2) * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(value_width - 10) * 10}" lengthAdjust="spacing">{value}</text>
    <text x="{(label_width + value_width // 2) * 10}" y="140" transform="scale(.1)" textLength="{(value_width - 10) * 10}" lengthAdjust="spacing">{value}</text>
  </g>
</svg>'''


def generate_badge_markdown(report: ScoreReport) -> str:
    """
    Generate README markdown for embedding the badge.
    Badge links to CSI verification page where anyone can re-scan.
    """
    if not report.badge_eligible:
        return (
            f"<!-- AI SAFE2 MCP Score: {report.total_score}/100 — "
            f"Score 70+ required for badge. Run mcp-score to improve. -->"
        )

    encoded_url = quote(report.server_url, safe="")
    verify_link = f"https://cyberstrategyinstitute.com/ai-safe2/mcp-verify?url={encoded_url}"

    # Shields.io badge (no local file needed for README embedding)
    color_name = {
        "Secure": "brightgreen",
        "Acceptable": "orange",
        "Elevated Risk": "yellow",
        "High Risk": "red",
        "Critical": "darkred",
    }.get(report.rating, "grey")

    label = quote("AI SAFE2 MCP", safe="")
    value = quote(f"Score: {report.total_score}/100 | {report.rating}", safe="")
    badge_url = f"https://img.shields.io/badge/{label}-{value}-{color_name}?style=for-the-badge"

    return f"""[![AI SAFE2 MCP Score: {report.total_score}/100]({badge_url})]({verify_link})"""


def generate_well_known_template(
    server_name: str,
    score: int,
    assessment_timestamp: str,
    no_dynamic_commands: bool = True,
    output_sanitization_lib: str = "aisafe2-mcp-tools>=1.0.0",
    source_hash: str = "",
    rate_limiting: bool = True,
    audit_logging: bool = True,
    network_isolation: str = "127.0.0.1 only",
) -> str:
    """
    Generate a .well-known/mcp-security.json template for builders.
    
    This file goes at: <your-server-root>/.well-known/mcp-security.json
    It is publicly accessible without authentication (it is not a secret).
    It attests to controls that cannot be verified remotely by mcp-score.
    
    Controls attested here receive bonus points during scoring:
      no_dynamic_commands  +8 pts  (MCP-1 — biggest remote blind spot)
      output_sanitization  +5 pts  (MCP-2 — library reference)
      source_hash          +4 pts  (MCP-4 — integrity verification)
      audit_logging        +4 pts  (MCP-5 — audit trail)
      network_isolation    +4 pts  (MCP-6 — localhost binding)
    
    These are builder attestations — they are not cryptographically verified
    by mcp-score. CSI recommends builders publish their source code so
    attestation claims can be independently verified.
    """
    data = {
        "mcp_security_version": "1.0",
        "framework": "AI SAFE2 v3.0 CP.5.MCP",
        "server_name": server_name,
        "aisafe2_score": score,
        "last_assessed": assessment_timestamp,
        "controls": {
            "MCP-1_no_dynamic_commands": no_dynamic_commands,
            "MCP-2_output_sanitization": output_sanitization_lib,
            "MCP-4_source_hash": source_hash or "COMPUTE_AND_FILL_IN",
            "MCP-5_audit_logging": audit_logging,
            "MCP-6_network_isolation": network_isolation,
            "MCP-6_rate_limiting": rate_limiting,
            "MCP-8_session_economics": False,
            "MCP-9_context_tool_isolation": "",
            "MCP-10_multi_agent_provenance": False,
            "MCP-11_schema_temporal_profiling": False,
            "MCP-12_swarm_c2_controls": False,
            "MCP-13_failure_taxonomy": False,
        },
        "attestation_note": (
            "These controls are builder-attested. "
            "Independent verification: run `mcp-score <your-server-url>` "
            "or visit cyberstrategyinstitute.com/ai-safe2/mcp-verify"
        ),
        "source_code": "FILL_IN_YOUR_REPO_URL",
        "contact": "FILL_IN_SECURITY_CONTACT_EMAIL",
    }
    return json.dumps(data, indent=2)


def generate_badge_report_section(report: ScoreReport) -> str:
    """
    Generate the full badge implementation guide for builders.
    Included at the end of mcp-score HTML and JSON output.
    """
    if not report.badge_eligible:
        lines = [
            "## Badge Status: Not Yet Eligible",
            "",
            f"Current score: {report.total_score}/100 (minimum 70 required)",
            "",
            "### How to Qualify",
            "",
            "Run `mcp-score --help` for remediation guidance on each failing check.",
            "Common quick wins:",
        ]
        failing = [c for c in report.checks if not c.passed]
        for check in failing[:3]:
            lines.append(f"  - Fix `{check.check_id}`: {check.detail[:80]}...")
        return "\n".join(lines)

    lines = [
        f"## Badge Status: ELIGIBLE (Score: {report.total_score}/100)",
        "",
        "### Step 1: Add .well-known/mcp-security.json to your server",
        "",
        "Create this file at your server root (publicly accessible, no auth):",
        "",
        "```json",
        generate_well_known_template(
            server_name=report.server_url,
            score=report.total_score,
            assessment_timestamp=report.assessment_timestamp,
            source_hash=report.attestation.source_hash or "COMPUTE_AND_FILL_IN",
        ),
        "```",
        "",
        "Compute your source hash:",
        "```bash",
        "python -c \"from mcp_server.auth import _compute_source_hash; print(_compute_source_hash())\"",
        "```",
        "",
        "### Step 2: Add the badge to your README",
        "",
        "```markdown",
        generate_badge_markdown(report),
        "```",
        "",
        "### Step 3: Re-scan to verify",
        "",
        "```bash",
        f"mcp-score {report.server_url} --output json",
        "```",
        "",
        "Anyone can verify your score by running the same command or visiting:",
        f"https://cyberstrategyinstitute.com/ai-safe2/mcp-verify?url={quote(report.server_url, safe='')}",
        "",
        "### Badge Policy",
        "",
        "- Badge is valid for 90 days from last scan date",
        "- Re-scan required after any server update that affects scored controls",
        "- CSI reserves the right to revoke badge eligibility if a critical vulnerability",
        "  is subsequently discovered in a badged server",
        "- Embedding the badge constitutes acceptance of these terms",
    ]
    return "\n".join(lines)
