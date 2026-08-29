"""Regression tests for AI SAFE2 v3.1 MCP scanner integration."""

from scanner.rules import ALL_RULES
from scanner.rules.mcp_profile import MCP_RULES


def test_v31_total_rule_count() -> None:
    """v3.1 adds 12 MCP profile rules to the existing 40-rule scanner."""
    assert len(ALL_RULES) == 52


def test_mcp_profile_rule_count() -> None:
    assert len(MCP_RULES) == 12


def test_mcp19_is_advisory() -> None:
    rules = [rule for rule in MCP_RULES if rule.control_id == "MCP-19"]
    assert len(rules) == 1
    assert rules[0].severity == "INFO"


def test_no_discover_presence_rule() -> None:
    """MCP 2026-07-28 does not require server/discover for conformance."""
    for rule in MCP_RULES:
        text = " ".join((
            rule.description,
            rule.remediation,
            rule.pattern or "",
        )).lower()
        assert "server/discover" not in text


def test_v31_profile_reaches_new_control_range() -> None:
    ids = {rule.control_id for rule in MCP_RULES}
    assert "MCP-16" in ids
    assert "MCP-18" in ids
    assert "MCP-19" in ids
