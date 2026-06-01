"""
nexus_sdk/agbom.py
NEXUS Dynamic Agent Bill of Materials (AgBOM) v0.3

Extends CycloneDX v1.6 / SPDX 2.3 / SWID to produce a real-time updating
inventory of every tool, model, capability, knowledge source, and dependency
an agent is currently using. Updates on every tool discovery event and signs
each version with the agent's AIM key, forming a cryptographic hash chain.

Why AgBOM matters:
    NEXUS AIM = signed capability declaration AT REGISTRATION TIME
    Production agents dynamically discover MCP servers and add tool connections.
    The AIM is a 6-week-old static snapshot; the AgBOM is live truth.

    ACS analysis identified this gap: "Agents that mutate their own tool
    surfaces break static manifests." AgBOM solves this structurally with
    NEXUS cryptographic provenance rather than just a runtime inventory feed.

Chain integrity:
    Each AgBOM version links to its predecessor via hash chain:
    version_n.parent_hash = SHA-256(version_n-1)
    The chain anchors to the signed AIM at version 0.
    Tampering any version invalidates all subsequent versions.

Formats:
    to_cyclonedx(): CycloneDX v1.6 JSON BOM format
    to_spdx():      SPDX 2.3 tag-value summary
    to_dict():      NEXUS-native format with full provenance

PRODUCTION:
    Sign with actual ML-DSA-65 key from AIM.
    Publish to ANS (Agent Name Service) endpoint on every update.
    Subscribe to AgBOM updates for supply chain monitoring.

TESTING:
    Stub signing preserves the hash chain contract.
    No network required; full API exercises all AgBOM operations.

Reference: CycloneDX v1.6, SPDX 2.3, SWID ISO 19770-2, NEXUS-A2A v0.3
AI SAFE2 v3.0: A2.3, A2.5, T3.1, T3.3 (supply chain security)
"""

from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ── AgBOM Component Types ─────────────────────────────────────────────────────

class AgBOMComponentType(str, Enum):
    """
    Component types in an AgBOM. Maps to CycloneDX component types where possible.
    Extends with agent-specific types not present in standard SBOM vocabularies.
    """
    # Standard types (CycloneDX-compatible)
    TOOL           = "tool"          # External tool (MCP server, API endpoint)
    MODEL          = "model"         # LLM or embedding model
    LIBRARY        = "library"       # Python package, SDK
    FRAMEWORK      = "framework"     # Agent framework (LangChain, CrewAI, etc.)
    CONTAINER      = "container"     # Docker image
    # Agent-specific extensions
    KNOWLEDGE_BASE = "knowledge_base"  # RAG corpus, vector store
    MEMORY_STORE   = "memory_store"    # External memory backend
    MCP_SERVER     = "mcp_server"      # MCP protocol server
    TRUST_ANCHOR   = "trust_anchor"    # SPIFFE trust domain, CA certificate
    DELEGATION_PEER = "delegation_peer" # Agent in delegation chain


@dataclass
class AgBOMComponent:
    """
    Single component in the AgBOM. CycloneDX v1.6-compatible with NEXUS extensions.

    For MCP_SERVER components:
        name = server identifier (e.g., "github-mcp-server")
        version = server version or digest
        supplier = registry URL or DID of server publisher
        capability_digest = SHA-256 of the server's tool manifest
        signed_manifest = True if server provides a NEXUS-verified manifest
    """
    name: str
    component_type: AgBOMComponentType
    version: Optional[str] = None
    supplier: Optional[str] = None
    description: Optional[str] = None

    # Supply chain integrity
    capability_digest: Optional[str] = None   # SHA-256 of capability manifest
    source_url: Optional[str] = None          # Registry or download URL
    signed_manifest: bool = False             # True if NEXUS/NCA-verified

    # Discovery context
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    discovered_by_session: Optional[str] = None  # Session where tool was discovered

    # CycloneDX compatibility
    purl: Optional[str] = None  # Package URL (pkg:mcp/server-name@version)
    bom_ref: str = field(default_factory=lambda: f"comp-{uuid.uuid4().hex[:8]}")

    def to_cyclonedx_component(self) -> dict:
        """Serialize to CycloneDX v1.6 component format."""
        comp: dict = {
            "bom-ref": self.bom_ref,
            "type": self.component_type.value,
            "name": self.name,
        }
        if self.version:
            comp["version"] = self.version
        if self.supplier:
            comp["supplier"] = {"name": self.supplier}
        if self.description:
            comp["description"] = self.description
        if self.purl:
            comp["purl"] = self.purl
        if self.capability_digest:
            comp["hashes"] = [{"alg": "SHA-256", "content": self.capability_digest}]
        if self.source_url:
            comp["externalReferences"] = [
                {"type": "distribution", "url": self.source_url}
            ]
        # NEXUS extensions (CycloneDX properties)
        properties = []
        if self.signed_manifest:
            properties.append({"name": "nexus:signedManifest", "value": "true"})
        if self.discovered_at:
            properties.append({"name": "nexus:discoveredAt", "value": self.discovered_at})
        if properties:
            comp["properties"] = properties
        return comp

    def to_dict(self) -> dict:
        return {k: v for k, v in {
            "bom_ref": self.bom_ref,
            "name": self.name,
            "type": self.component_type.value,
            "version": self.version,
            "supplier": self.supplier,
            "description": self.description,
            "capability_digest": self.capability_digest,
            "source_url": self.source_url,
            "signed_manifest": self.signed_manifest,
            "discovered_at": self.discovered_at,
            "purl": self.purl,
        }.items() if v is not None}


# ── AgBOM Version ─────────────────────────────────────────────────────────────

@dataclass
class AgBOMVersion:
    """
    A single version in the AgBOM hash chain.
    Each version captures the COMPLETE current state, not a diff.
    Diffs are derivable; full snapshots are forensically complete.
    """
    version: int
    agent_did: str
    components: list[AgBOMComponent]
    parent_hash: Optional[str]  # None for v0 (anchors to AIM)

    bom_id: str = field(default_factory=lambda: f"agbom-{uuid.uuid4().hex[:16]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    change_reason: Optional[str] = None  # "mcp_server_discovered", "tool_removed", etc.

    # Populated after signing
    version_hash: Optional[str] = None
    signature: Optional[str] = None

    def compute_version_hash(self) -> str:
        """
        Compute SHA-256 over this version's canonical content.
        Hash chain: version_hash = SHA-256(parent_hash + agent_did + version + components_digest)
        Tampering any component invalidates this version and all successors.
        """
        components_digest = hashlib.sha256(
            json.dumps([c.to_dict() for c in sorted(self.components, key=lambda x: x.bom_ref)],
                       sort_keys=True).encode()
        ).hexdigest()

        chain_input = json.dumps({
            "parent_hash": self.parent_hash or "GENESIS",
            "agent_did": self.agent_did,
            "version": self.version,
            "timestamp": self.timestamp,
            "components_digest": components_digest,
        }, sort_keys=True)
        self.version_hash = hashlib.sha256(chain_input.encode()).hexdigest()
        return self.version_hash

    def sign(self) -> "AgBOMVersion":
        """
        Sign this version with the agent's AIM key.
        PRODUCTION: Use ML-DSA-65 key from AIM.
        TESTING: SHA-256 stub preserves chain integrity contract.
        """
        self.compute_version_hash()
        # PRODUCTION: self.signature = mldsa65_sign(aim_private_key, version_hash)
        self.signature = f"agbom-stub-{self.version_hash[:32]}"
        return self

    def verify_chain(self, parent_version: Optional["AgBOMVersion"]) -> bool:
        """
        Verify this version's hash chain integrity.
        Returns False if the chain has been tampered.
        """
        if parent_version is None:
            # v0: parent_hash must be None
            return self.parent_hash is None

        if not parent_version.version_hash:
            parent_version.compute_version_hash()

        return self.parent_hash == parent_version.version_hash


# ── AgBOM Manager ─────────────────────────────────────────────────────────────

class AgBOMManager:
    """
    Manages the dynamic AgBOM for a single agent.
    Maintains a hash-chained version history with cryptographic provenance.

    Every component discovery or removal:
      1. Creates a new AgBOMVersion with current full component set
      2. Sets parent_hash to the previous version's hash
      3. Signs the new version with the agent's AIM key
      4. Appends to version history

    PRODUCTION:
        Publish each new version to the ANS endpoint for external monitoring.
        Version history is append-only; never delete historical versions.
    """

    def __init__(self, agent_did: str, aim_digest: Optional[str] = None,
                 session_id: Optional[str] = None):
        self.agent_did = agent_did
        self.aim_digest = aim_digest
        self.session_id = session_id or str(uuid.uuid4())
        self._components: dict[str, AgBOMComponent] = {}  # bom_ref -> component
        self._version_history: list[AgBOMVersion] = []
        self._current_version = 0

    @property
    def component_count(self) -> int:
        return len(self._components)

    @property
    def current_version(self) -> int:
        return self._current_version

    @property
    def latest_version_hash(self) -> Optional[str]:
        if self._version_history:
            return self._version_history[-1].version_hash
        return None

    def add_component(self, component: AgBOMComponent,
                      reason: str = "component_added") -> AgBOMVersion:
        """
        Register a new component. Creates a new signed AgBOM version.
        Called when an agent discovers a new MCP server or tool.
        """
        component.discovered_by_session = self.session_id
        self._components[component.bom_ref] = component
        return self._snapshot(reason)

    def remove_component(self, bom_ref: str,
                          reason: str = "component_removed") -> Optional[AgBOMVersion]:
        """Remove a component and create a new version."""
        if bom_ref not in self._components:
            return None
        del self._components[bom_ref]
        return self._snapshot(reason)

    def discover_mcp_server(self, server_name: str, server_url: str,
                             tool_manifest_digest: Optional[str] = None,
                             version: Optional[str] = None,
                             signed: bool = False) -> AgBOMVersion:
        """
        Register a newly-discovered MCP server as an AgBOM component.
        Sets purl in pkg:mcp/ namespace for standardized reference.
        """
        component = AgBOMComponent(
            name=server_name,
            component_type=AgBOMComponentType.MCP_SERVER,
            version=version,
            supplier=server_url,
            capability_digest=tool_manifest_digest,
            source_url=server_url,
            signed_manifest=signed,
            purl=f"pkg:mcp/{server_name}{'@' + version if version else ''}",
        )
        return self.add_component(component, reason="mcp_server_discovered")

    def _snapshot(self, change_reason: str) -> AgBOMVersion:
        """Create a signed AgBOM version snapshot."""
        parent_hash = self._version_history[-1].version_hash if self._version_history else None
        self._current_version += 1

        version = AgBOMVersion(
            version=self._current_version,
            agent_did=self.agent_did,
            components=list(self._components.values()),
            parent_hash=parent_hash,
            change_reason=change_reason,
        )
        version.sign()
        self._version_history.append(version)
        return version

    def verify_chain_integrity(self) -> tuple[bool, list[str]]:
        """
        Verify the complete hash chain integrity.
        Returns (is_valid, list_of_violations).
        An empty violations list means the chain is intact.
        """
        violations: list[str] = []

        for i, version in enumerate(self._version_history):
            parent = self._version_history[i - 1] if i > 0 else None
            if not version.verify_chain(parent):
                violations.append(
                    f"Version {version.version} hash chain broken "
                    f"(expected parent={parent.version_hash[:16] if parent and parent.version_hash else 'None'})"
                )
            if not version.version_hash:
                violations.append(f"Version {version.version} missing version_hash")

        return (len(violations) == 0, violations)

    def get_mcp_servers(self) -> list[AgBOMComponent]:
        """Return all currently registered MCP servers."""
        return [c for c in self._components.values()
                if c.component_type == AgBOMComponentType.MCP_SERVER]

    def get_unsigned_components(self) -> list[AgBOMComponent]:
        """Return components without signed manifests (supply chain risk)."""
        return [c for c in self._components.values()
                if c.component_type == AgBOMComponentType.MCP_SERVER
                and not c.signed_manifest]

    def to_cyclonedx(self) -> dict:
        """
        Serialize current AgBOM state to CycloneDX v1.6 JSON BOM format.
        This is the format consumed by Grype, DependencyTrack, and standard SCA tooling.
        """
        latest = self._version_history[-1] if self._version_history else None
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "version": self._current_version,
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tools": [{"vendor": "Cyber Strategy Institute", "name": "NEXUS-A2A", "version": "0.3.0"}],
                "component": {
                    "type": "application",
                    "name": self.agent_did.split(":")[-1],
                    "description": self.agent_did,
                    "properties": [
                        {"name": "nexus:agentDID", "value": self.agent_did},
                        {"name": "nexus:agbomVersion", "value": str(self._current_version)},
                        {"name": "nexus:chainHash", "value": latest.version_hash or "" if latest else ""},
                    ],
                },
            },
            "components": [c.to_cyclonedx_component() for c in self._components.values()],
        }

    def to_spdx_summary(self) -> str:
        """Serialize to SPDX 2.3 tag-value summary format."""
        lines = [
            "SPDXVersion: SPDX-2.3",
            "DataLicense: CC0-1.0",
            f"SPDXID: SPDXRef-DOCUMENT",
            f"DocumentName: nexus-agbom-{self.agent_did.split(':')[-1]}",
            f"DocumentNamespace: https://nexus-protocol.csi.gov/agbom/{uuid.uuid4()}",
            f"Creator: Tool: NEXUS-A2A-0.3.0",
            f"Created: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "",
        ]
        for comp in self._components.values():
            lines += [
                f"PackageName: {comp.name}",
                f"SPDXID: SPDXRef-{comp.bom_ref}",
                f"PackageVersion: {comp.version or 'NOASSERTION'}",
                f"PackageDownloadLocation: {comp.source_url or 'NOASSERTION'}",
                f"FilesAnalyzed: false",
                f"PackageComment: nexus:type={comp.component_type.value}",
                "",
            ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """NEXUS-native AgBOM format with full provenance."""
        latest = self._version_history[-1] if self._version_history else None
        return {
            "agbom_format": "nexus-agbom/0.3",
            "agent_did": self.agent_did,
            "aim_digest": self.aim_digest,
            "current_version": self._current_version,
            "latest_version_hash": latest.version_hash if latest else None,
            "component_count": self.component_count,
            "components": [c.to_dict() for c in self._components.values()],
            "unsigned_mcp_server_count": len(self.get_unsigned_components()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
