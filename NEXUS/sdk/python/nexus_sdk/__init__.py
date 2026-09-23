"""
nexus_sdk - NEXUS-A2A Python SDK
Cyber Strategy Institute | v0.4.0 | AI SAFE2 v3.1 Compatible

v0.4 additions:
    payments/    CP.5.APAY agent-to-payment enforcement plane. Imported
                 explicitly (`from nexus_sdk.payments import ...`) rather than
                 re-exported here, so a deployment that does not move value
                 does not load the payment object model.

                 The default credential broker REFUSES every signing request.
                 An unconfigured payment path does not move money.

v0.3 additions:
    guardian.py  - ACS-compatible Guardian Integration Profile (per-call verdict model)
    otel.py      - OpenTelemetry-native NOR export with OCSF mapping (SIEM-native audit)
    agbom.py     - Dynamic Agent Bill of Materials (real-time, hash-chained, CycloneDX)
    bridges:acs  - NEXUS-ACS Bridge Specification v0.1 (AOS JSON-RPC 2.0)

Quick start:
    from nexus_sdk.cael import CAELEnvelope, CAELSender, Performative
    from nexus_sdk.memory import MemoryVaccine, MemoryZone
    from nexus_sdk.guardian import GuardianPolicy, build_tool_call_step
    from nexus_sdk.otel import InMemoryNORExporter, build_tool_call_nor
    from nexus_sdk.agbom import AgBOMManager
    from nexus_sdk.bridges import ProtocolBridgeFactory

Full docs: https://github.com/CyberStrategyInstitute/ai-safe2-framework/nexus-a2a
"""
from nexus_sdk.cael import (
    CAELEnvelope, CAELSender, CAELPolicy, CAELBudget, CAELDelegation,
    CAELMemory, CAELToolCall, JouleWorkCost, OPAReceipt,
    Performative, ContextCompartment,
)
from nexus_sdk.memory import (
    MemoryVaccine, MemoryZone, MemoryWriteResult, JouleWorkAccount,
)
from nexus_sdk.guardian import (
    GuardianPolicy, GuardianVerdict, GuardianVerdictResult,
    GuardianStepContext, NEXUSAgentContext, NEXUSMemoryProvenance,
    StepMethod, NEXUSGuardianClient,
    build_tool_call_step, build_memory_store_step,
)
from nexus_sdk.otel import (
    NEXUSOutputReceipt, InMemoryNORExporter, NEXUSNORSpan,
    OCSFEventClass, build_tool_call_nor, build_memory_nor,
)
from nexus_sdk.agbom import (
    AgBOMManager, AgBOMComponent, AgBOMComponentType,
)
from nexus_sdk.bridges import (
    NEXUSMCPBridge, NEXUSACSBridge, NEXUSAIBridge, NEXUSOpenAIBridge,
    NEXUSRESTBridge, ProtocolBridgeFactory,
)

__version__ = "0.4.0"
__all__ = [
    # CAEL core
    "CAELEnvelope", "CAELSender", "CAELPolicy", "CAELBudget", "CAELDelegation",
    "CAELMemory", "CAELToolCall", "JouleWorkCost", "OPAReceipt",
    "Performative", "ContextCompartment",
    # Memory
    "MemoryVaccine", "MemoryZone", "MemoryWriteResult", "JouleWorkAccount",
    # Guardian (v0.3)
    "GuardianPolicy", "GuardianVerdict", "GuardianVerdictResult",
    "GuardianStepContext", "NEXUSAgentContext", "NEXUSMemoryProvenance",
    "StepMethod", "NEXUSGuardianClient",
    "build_tool_call_step", "build_memory_store_step",
    # OTel NOR (v0.3)
    "NEXUSOutputReceipt", "InMemoryNORExporter", "NEXUSNORSpan",
    "OCSFEventClass", "build_tool_call_nor", "build_memory_nor",
    # AgBOM (v0.3)
    "AgBOMManager", "AgBOMComponent", "AgBOMComponentType",
    # Bridges
    "NEXUSMCPBridge", "NEXUSACSBridge", "NEXUSAIBridge", "NEXUSOpenAIBridge",
    "NEXUSRESTBridge", "ProtocolBridgeFactory",
]
