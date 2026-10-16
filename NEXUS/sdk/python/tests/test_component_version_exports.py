"""Generated provenance must identify the actual SDK rather than an old release."""

import nexus_sdk
from nexus_sdk.agbom import AgBOMManager


def test_agbom_producer_version_matches_sdk():
    manager = AgBOMManager("did:nexus:agent:version-test")
    assert manager.to_cyclonedx()["metadata"]["tools"][0]["version"] == nexus_sdk.__version__
    assert f"Creator: Tool: NEXUS-A2A-{nexus_sdk.__version__}" in manager.to_spdx_summary()
    # Wire-format identity is independent of the producing implementation.
    assert manager.to_dict()["agbom_format"] == "nexus-agbom/0.3"


def test_producer_uses_runtime_version_instead_of_a_release_literal(monkeypatch):
    monkeypatch.setattr(nexus_sdk, "__version__", "99.2.1")
    manager = AgBOMManager("did:nexus:agent:version-test")
    assert manager.to_cyclonedx()["metadata"]["tools"][0]["version"] == "99.2.1"
    assert "Creator: Tool: NEXUS-A2A-99.2.1" in manager.to_spdx_summary()
