"""
nexus_sdk/bridges/__init__.py
NEXUS-A2A Protocol Bridges v0.3

Bridge architecture: "Internal richness, external compatibility"
- CAEL carries everything internally
- Each bridge extracts what the external protocol supports
- NEXUS context passes in _meta / metadata fields (ignored by non-NEXUS endpoints)
- Full CAEL envelope preserved in gateway for audit regardless

v0.3 additions:
- NEXUSACSBridge: NEXUS-ACS Bridge Specification v0.1 (AOS JSON-RPC 2.0)
  Translates CAEL envelopes to ACS Guardian requests with NEXUS identity binding.
  See NEXUS vs ACS analysis, Part VII for integration architecture.

Compatible with:
- MCP (Model Context Protocol) - HTTP + SSE, _meta extension
- ACS / AOS (Agent Control Standard / Agent Operation Spec) - JSON-RPC 2.0
- Google A2A - Agent Cards + HTTP, task metadata fields
- OpenAI function-calling - tool_calls array, metadata field
- OpenClaw - HTTP REST + plugin RPC, x-nexus headers
- LangChain/LangGraph - Python tool wrapping
- CrewAI - agent tool wrapping
- n8n - HTTP node + webhook headers
- Generic REST - x-nexus-* headers

Reference: NEXUS-A2A Spec v0.3 Part VII / Part IX
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


class NEXUSMCPBridge:
    """
    MCP (Model Context Protocol) bridge.
    Preserves NEXUS context in _meta fields.
    Non-NEXUS MCP servers silently ignore _meta.nexus* fields.
    NEXUS-aware MCP servers consume delegation provenance and mandate IDs.

    MCP 2026-07-28 RC adds stateless core (session handshake removed) and
    authorization hardening (RFC 9207 iss validation). The _meta extension
    pattern is preserved and compatible with both 2025-11-25 and 2026 RC.

    Compatible with: Claude Code MCP, Anthropic tools, any MCP server
    """

    def build_mcp_request(self, cael_tool_call: dict,
                          mcp_server_url: str) -> dict:
        """
        Translate CAEL tool call to MCP tools/call request.
        NEXUS context goes in params._meta (non-breaking for existing servers).
        """
        provenance = cael_tool_call.get("provenance", {})
        jw = cael_tool_call.get("joulework", {})
        opa = cael_tool_call.get("opa_auth", {})

        return {
            "jsonrpc": "2.0",
            "id": cael_tool_call.get("tool_call_id"),
            "method": "tools/call",
            "params": {
                "name": cael_tool_call["tool_name"],
                "arguments": cael_tool_call["arguments"],
                "_meta": {
                    # NEXUS context - ignored by non-NEXUS MCP servers
                    "nexusTraceId": cael_tool_call.get("trace_id"),
                    "nexusDelegationDepth": provenance.get("delegation_depth", 0),
                    "nexusVCCId": provenance.get("vcc_id"),
                    "nexusContextCompartment": provenance.get("context_compartment"),
                    "nexusJWCost": jw.get("estimated_cost_jw"),
                    "nexusMandateId": cael_tool_call.get("approval", {}).get("mandate_id"),
                    "nexusOPAReceipt": opa.get("decision_timestamp"),
                    "nexusIdempotencyKey": cael_tool_call.get("idempotency_key"),
                    "nexusPolicyVersion": opa.get("policy_version"),
                }
            }
        }

    def wrap_mcp_result(self, mcp_result: dict, tool_call_id: str) -> dict:
        """Wrap MCP result as NEXUS CAEL artifact with provenance."""
        return {
            "artifact_type": "mcp_tool_result",
            "tool_call_id": tool_call_id,
            "content": mcp_result.get("result", mcp_result),
            "nexus_wrapped": True,
            "source_protocol": "mcp",
        }

    async def invoke(self, cael_tool_call: dict, mcp_server_url: str) -> dict:
        """
        Full async MCP invocation. Requires httpx in production.
        TESTING: Use build_mcp_request() to validate the translation contract.
        """
        try:
            import httpx
            mcp_request = self.build_mcp_request(cael_tool_call, mcp_server_url)
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(mcp_server_url, json=mcp_request)
                resp.raise_for_status()
                return self.wrap_mcp_result(
                    resp.json(), cael_tool_call.get("tool_call_id", "")
                )
        except ImportError:
            return {"error": "httpx required for async invocation: pip install httpx",
                    "mcp_request": self.build_mcp_request(cael_tool_call, mcp_server_url)}


class NEXUSACSBridge:
    """
    NEXUS-ACS Bridge Specification v0.1
    Translates NEXUS CAEL envelopes to AOS (Agent Operation Spec) JSON-RPC 2.0
    Guardian requests and interprets Guardian verdicts back into NEXUS decisions.

    Key architectural contribution over ACS v0.1.0:
        ACS StepContext.agent = { id: string }       (unauthenticated bare string)
        NEXUS StepContext.agent via this bridge       (DID + SPIFFE, provenance-linked)

    ACS Guardians that don't understand the nexus extension block see valid AOS
    StepContext. The identity enhancement is backward-compatible.

    The critical gap this fills: ACS's Guardian intercepts per-call arguments;
    NEXUS OPA enforces capability categories. Together = the L3 stack that
    catches "legitimate credential, illegitimate specific argument" attacks.

    Deployment: place between NEXUS agent and any ACS-compatible Guardian.
    Reference: ACS v0.1.0, AOS v0.1.0 (aos.owasp.org), NEXUS-A2A v0.3
    AI SAFE2 v3.0: S1.3, F3.1, CP.4, CP.5.MCP-7
    """

    def build_tool_call_request(self, cael_tool_call: dict,
                                 reasoning: Optional[str] = None) -> dict:
        """
        Translate CAEL tool call to AOS steps/toolCallRequest JSON-RPC 2.0.
        Interception point: AFTER LLM inference, BEFORE tool execution.
        The Guardian sees actual arguments the LLM chose, not just capability scope.
        """
        provenance = cael_tool_call.get("provenance", {})
        step_id = f"step_{cael_tool_call.get('tool_call_id', uuid.uuid4().hex[:12])}"
        agent_did = provenance.get("requested_by_did", "")

        params: dict[str, Any] = {
            "stepId": step_id,
            "sessionId": f"sess_{agent_did[-8:]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": {
                "id": agent_did,        # ACS compatibility (bare id field)
                "agent_did": agent_did, # NEXUS extension
                # spiffe_id populated from AIM lookup in production
            },
            "action": {
                "method": cael_tool_call.get("tool_name", ""),
                "arguments": cael_tool_call.get("arguments", {}),
            },
        }

        if reasoning:
            params["reasoning"] = reasoning

        # NEXUS extension block (ignored by ACS-only Guardians)
        nexus_ext: dict[str, Any] = {
            "delegationDepth": provenance.get("delegation_depth", 0),
        }
        if provenance.get("vcc_id"):
            nexus_ext["vccId"] = provenance["vcc_id"]
        if provenance.get("context_compartment"):
            nexus_ext["contextCompartment"] = provenance["context_compartment"]
        if cael_tool_call.get("opa_auth"):
            nexus_ext["opaReceipt"] = cael_tool_call["opa_auth"]
        params["nexus"] = nexus_ext

        return {
            "jsonrpc": "2.0",
            "id": step_id,
            "method": "steps/toolCallRequest",
            "params": params,
        }

    def build_memory_store_request(self, content: list[str],
                                    agent_did: str,
                                    provenance_dict: Optional[dict] = None) -> dict:
        """
        Translate memory write to AOS steps/memoryStore with NEXUS provenance.
        Provenance metadata enables Guardian memory policies ACS alone cannot enforce:
          - drift_score enforcement (tighter than Vaccine's default threshold)
          - stale checkpoint detection (>48h since last checkpoint)
          - zone-based mandate verification
        """
        step_id = f"step_mem_{uuid.uuid4().hex[:12]}"
        params: dict[str, Any] = {
            "stepId": step_id,
            "sessionId": f"sess_{agent_did[-8:]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": {"id": agent_did, "agent_did": agent_did},
            "memory": content,
        }
        if provenance_dict:
            params["nexus"] = {"memoryProvenance": provenance_dict}

        return {
            "jsonrpc": "2.0",
            "id": step_id,
            "method": "steps/memoryStore",
            "params": params,
        }

    def build_message_request(self, cael_envelope: dict,
                               direction: str = "input") -> dict:
        """
        Translate CAEL message to AOS steps/message request.
        direction: "input" = before reaching agent; "output" = before reaching user
        """
        step_id = f"step_msg_{cael_envelope.get('message_id', uuid.uuid4().hex[:12])}"
        sender = cael_envelope.get("sender", {})

        return {
            "jsonrpc": "2.0",
            "id": step_id,
            "method": "steps/message",
            "params": {
                "stepId": step_id,
                "sessionId": cael_envelope.get("thread_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": {
                    "id": sender.get("agent_did", ""),
                    "agent_did": sender.get("agent_did", ""),
                },
                "action": {
                    "method": f"message.{direction}",
                    "arguments": {
                        "performative": cael_envelope.get("performative"),
                        "goal": cael_envelope.get("content", {}).get("goal", ""),
                    },
                },
                "nexus": {
                    "traceId": cael_envelope.get("trace", {}).get("trace_id"),
                    "delegationDepth": cael_envelope.get("delegation", {}).get("delegation_depth", 0),
                    "caelEnvelopeHash": cael_envelope.get("content_hash"),
                },
            },
        }

    def parse_verdict(self, jsonrpc_response: dict) -> dict:
        """
        Parse AOS JSON-RPC 2.0 Guardian response into a NEXUS policy decision.
        Returns normalized dict compatible with NEXUS policy chain.
        """
        if "error" in jsonrpc_response:
            return {
                "allowed": False,
                "decision": "deny",
                "reason_codes": ["GUARDIAN_ERROR"],
                "error": jsonrpc_response["error"],
            }
        result = jsonrpc_response.get("result", {})
        decision = result.get("decision", "deny")
        return {
            "allowed": decision == "allow",
            "decision": decision,
            "reason_codes": result.get("reasonCode", []),
            "reasoning": result.get("reasoning"),
            "modified_request": result.get("modifiedRequest"),
            "step_id": jsonrpc_response.get("id"),
            "nor_fingerprint": result.get("norFingerprint"),
        }

    async def evaluate_tool_call(self, cael_tool_call: dict,
                                  guardian_url: str,
                                  reasoning: Optional[str] = None) -> dict:
        """
        Full async Guardian evaluation for a tool call.
        TESTING: Use parse_verdict(build_tool_call_request(...)) to test the contract.
        """
        try:
            import httpx
            request = self.build_tool_call_request(cael_tool_call, reasoning)
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(guardian_url, json=request)
                resp.raise_for_status()
                return self.parse_verdict(resp.json())
        except ImportError:
            return {
                "error": "httpx required for async evaluation: pip install httpx",
                "request": self.build_tool_call_request(cael_tool_call, reasoning),
            }


class NEXUSAIBridge:
    """
    Google A2A bridge.
    A2A uses Agent Cards (.well-known/agent.json), HTTP + SSE, OAuth 2.0 / mTLS.
    NEXUS imports external A2A Agent Cards as AIMs with maturityLevel='external'.
    NEXUS context passes in task.message.metadata fields.

    Compatible with: Google Vertex AI Agent Builder, Google ADK, A2A SDK,
    any agent exposing .well-known/agent.json

    Reference: A2A Protocol - https://a2aprotocol.ai/docs/
    """

    def build_a2a_task(self, cael_envelope: dict) -> dict:
        """
        Translate CAEL envelope to A2A task.
        NEXUS context goes in message.metadata.
        """
        policy = cael_envelope.get("policy", {})
        delegation = cael_envelope.get("delegation", {})
        trace = cael_envelope.get("trace", {})
        budget = policy.get("budget", {})

        return {
            "message": {
                "role": "user",
                "parts": [{"type": "text",
                            "text": cael_envelope.get("content", {}).get("goal", "")}],
                "metadata": {
                    "nexusSenderDID": cael_envelope.get("sender", {}).get("agent_did"),
                    "nexusSpiffeId": cael_envelope.get("sender", {}).get("spiffe_id"),
                    "nexusVCCId": delegation.get("vcc_id"),
                    "nexusDelegationDepth": delegation.get("delegation_depth", 0),
                    "nexusTraceId": trace.get("trace_id"),
                    "nexusCausalChain": trace.get("causal_chain", []),
                    "nexusJurisdiction": policy.get("jurisdiction", []),
                    "nexusJWBudget": budget.get("max_joulework"),
                    "nexusMandateRequired": policy.get("mandate_required", []),
                    "nexusClassification": policy.get("classification"),
                    "nexusContextCompartment": cael_envelope.get("memory", {}).get("context_compartment"),
                }
            }
        }

    async def send_task(self, cael_envelope: dict, remote_agent_card_url: str) -> dict:
        """
        Full async A2A task submission.
        TESTING: Use build_a2a_task() to validate translation contract.
        """
        try:
            import httpx
            a2a_task = self.build_a2a_task(cael_envelope)
            async with httpx.AsyncClient(timeout=30.0) as client:
                card_resp = await client.get(remote_agent_card_url)
                card_resp.raise_for_status()
                agent_card = card_resp.json()
                task_url = f"{agent_card.get('url', '')}/tasks"
                resp = await client.post(task_url, json=a2a_task)
                resp.raise_for_status()
                return resp.json()
        except ImportError:
            return {"error": "httpx required: pip install httpx",
                    "a2a_task": self.build_a2a_task(cael_envelope)}


class NEXUSOpenAIBridge:
    """
    OpenAI function-calling / tool-calling bridge.
    Translates CAEL tool calls to OpenAI's tool_calls format.
    NEXUS context passes in the metadata field.

    Compatible with: OpenAI Agents SDK, OpenAI API direct, any OpenAI-compatible API
    Also compatible with: Anthropic tool-use (same pattern, different field names)

    Reference: OpenAI tool-calling schema 2025-04
    """

    def build_openai_tool_call(self, cael_tool_call: dict) -> dict:
        import json as _json
        provenance = cael_tool_call.get("provenance", {})
        jw = cael_tool_call.get("joulework", {})
        return {
            "id": cael_tool_call.get("tool_call_id"),
            "type": "function",
            "function": {
                "name": cael_tool_call["tool_name"],
                "arguments": _json.dumps(cael_tool_call["arguments"]),
            },
            "metadata": {
                "nexus_delegation_depth": provenance.get("delegation_depth", 0),
                "nexus_vcc_id": provenance.get("vcc_id"),
                "nexus_context": provenance.get("context_compartment"),
                "nexus_jw_cost": jw.get("estimated_cost_jw"),
                "nexus_idempotency_key": cael_tool_call.get("idempotency_key"),
            }
        }

    def wrap_for_langchain(self, cael_tool_call: dict) -> dict:
        return {
            "tool": cael_tool_call["tool_name"],
            "tool_input": cael_tool_call["arguments"],
            "tool_call_id": cael_tool_call.get("tool_call_id"),
            "nexus_provenance": cael_tool_call.get("provenance", {}),
        }

    def wrap_for_crewai(self, cael_tool_call: dict) -> dict:
        return {
            "tool_name": cael_tool_call["tool_name"],
            "arguments": cael_tool_call["arguments"],
            "context": {
                "nexus_vcc_id": cael_tool_call.get("provenance", {}).get("vcc_id"),
                "nexus_delegation_depth": cael_tool_call.get("provenance", {}).get("delegation_depth"),
            }
        }


class NEXUSRESTBridge:
    """
    Generic REST bridge. Passes NEXUS context in x-nexus-* headers.
    Works with: n8n HTTP nodes, webhook targets, OpenClaw plugins, any REST endpoint.
    """

    def build_rest_request(self, cael_envelope: dict, endpoint_url: str,
                           http_method: str = "POST") -> dict:
        policy = cael_envelope.get("policy", {})
        delegation = cael_envelope.get("delegation", {})
        trace = cael_envelope.get("trace", {})
        budget = policy.get("budget", {})

        headers = {
            "Content-Type": "application/json",
            "X-Nexus-Sender-DID": cael_envelope.get("sender", {}).get("agent_did", ""),
            "X-Nexus-Trace-ID": trace.get("trace_id", ""),
            "X-Nexus-Delegation-Depth": str(delegation.get("delegation_depth", 0)),
            "X-Nexus-VCC-ID": delegation.get("vcc_id", ""),
            "X-Nexus-Classification": policy.get("classification", "internal"),
            "X-Nexus-Jurisdiction": ",".join(policy.get("jurisdiction", [])),
            "X-Nexus-JW-Budget": str(budget.get("max_joulework", "")),
            "X-Nexus-Mandate-Required": ",".join(policy.get("mandate_required", [])),
            "X-Nexus-Context-Compartment": cael_envelope.get("memory", {}).get("context_compartment", ""),
        }
        headers = {k: v for k, v in headers.items() if v and v != "0"}

        return {
            "method": http_method,
            "url": endpoint_url,
            "headers": headers,
            "json": cael_envelope.get("content", {}),
        }

    def build_n8n_headers(self, cael_envelope: dict) -> dict:
        req = self.build_rest_request(cael_envelope, "")
        return req["headers"]


class ProtocolBridgeFactory:
    """
    Factory for getting the right bridge for an agent/endpoint.
    v0.3: adds ACS bridge support.
    """
    _mcp = NEXUSMCPBridge()
    _acs = NEXUSACSBridge()
    _a2a = NEXUSAIBridge()
    _openai = NEXUSOpenAIBridge()
    _rest = NEXUSRESTBridge()

    @classmethod
    def get_bridge(cls, protocol: str):
        bridges = {
            "mcp": cls._mcp,
            "acs": cls._acs,
            "a2a": cls._a2a,
            "openai": cls._openai,
            "langchain": cls._openai,
            "crewai": cls._openai,
            "n8n": cls._rest,
            "rest": cls._rest,
            "openclaw": cls._rest,
            "browser-use": cls._rest,
        }
        bridge = bridges.get(protocol.lower())
        if not bridge:
            raise ValueError(
                f"Unknown protocol: {protocol}. "
                f"Supported: {list(bridges.keys())}"
            )
        return bridge

    @classmethod
    def detect_protocol(cls, agent_config: dict) -> str:
        if agent_config.get("mcp_server_url"):
            return "mcp"
        if agent_config.get("a2a_card") or agent_config.get("a2a_peer_url"):
            return "a2a"
        if agent_config.get("guardian_url"):
            return "acs"
        if agent_config.get("openai_api_key") or agent_config.get("anthropic_api_key"):
            return "openai"
        if agent_config.get("n8n_webhook_url"):
            return "n8n"
        return "rest"
