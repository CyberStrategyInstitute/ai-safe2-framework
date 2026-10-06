"""AgBOM integrity regression suite (2026-10-06 false-assurance battery).

v0.3 verified the chain by comparing stored hashes only, shared live component
objects across snapshots, and registered a changed tool manifest as a second,
trusted server. A tampered history verified as intact and a rug pull went unseen.
"""
from nexus_sdk.agbom import AgBOMManager

A, B, C = "a" * 64, "b" * 64, "c" * 64


def fresh():
    m = AgBOMManager("did:nexus:agent:t")
    m.discover_mcp_server("fs-mcp", "https://fs.example/mcp", tool_manifest_digest=A, version="1")
    m.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest=B, version="1")
    return m


def test_clean_chain_verifies():
    ok, violations = fresh().verify_chain_integrity()
    assert ok and violations == []


def test_tampered_historical_component_is_detected():
    m = fresh()
    m._version_history[0].components[0].supplier = "https://evil.example/mcp"
    ok, violations = m.verify_chain_integrity()
    assert not ok
    assert any("version 1" in v.lower() for v in violations)


def test_tampered_latest_component_is_detected():
    m = fresh()
    m._version_history[-1].components[-1].capability_digest = "f" * 64
    assert not m.verify_chain_integrity()[0]


def test_snapshots_are_isolated_from_live_edits():
    m = fresh()
    before = m._version_history[0].components[0].supplier
    for c in m.get_mcp_servers():
        c.supplier = "https://changed.example"
    assert m._version_history[0].components[0].supplier == before
    assert m.verify_chain_integrity()[0]


def test_rug_pull_is_quarantined_not_trusted():
    m = fresh()
    v = m.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest=C, version="1")
    assert v.change_reason == "mcp_capability_digest_changed"
    wx = [c for c in m.get_mcp_servers() if c.name == "wx-mcp"]
    assert len(wx) == 1, "a changed manifest must not create a second trusted server"
    assert wx[0].quarantined and wx[0].capability_digest == C and wx[0].previous_capability_digest == B
    assert [c.name for c in m.get_quarantined_components()] == ["wx-mcp"]
    assert m.verify_chain_integrity()[0]


def test_quarantine_release_is_an_explicit_recorded_decision():
    m = fresh()
    m.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest=C)
    ref = m.get_quarantined_components()[0].bom_ref
    v = m.approve_capability_change(ref, approver="owner@example.org")
    assert v.change_reason == "capability_change_approved:owner@example.org"
    assert m.get_quarantined_components() == []
    assert m.verify_chain_integrity()[0]


def test_unchanged_rediscovery_is_idempotent():
    m = fresh()
    n = m.current_version
    m.discover_mcp_server("wx-mcp", "https://wx.example/mcp", tool_manifest_digest=B, version="1")
    assert m.current_version == n
    assert m.get_quarantined_components() == []


def test_first_digest_pins_without_quarantine():
    m = AgBOMManager("did:nexus:agent:t")
    m.discover_mcp_server("anon", "https://anon.example/mcp")
    v = m.discover_mcp_server("anon", "https://anon.example/mcp", tool_manifest_digest=A)
    assert v.change_reason == "mcp_capability_digest_pinned"
    assert m.get_quarantined_components() == []


def test_unpinned_server_is_reported():
    m = AgBOMManager("did:nexus:agent:t")
    m.discover_mcp_server("anon", "https://anon.example/mcp")
    assert len(m.get_unsigned_components()) == 1
