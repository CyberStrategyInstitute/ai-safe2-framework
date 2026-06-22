"""
AI SAFE² v3.0 — LangGraph Sovereign Enforcement Layer
======================================================
LangGraph's threat surface differs fundamentally from LangChain's.
There is no BaseCallbackHandler. Enforcement hooks into node functions directly.

THREE UNIQUE SURFACES vs LangChain:

  1. State dict injection at node boundaries (P1.T1.10 + S1.3)
     The `state` dict flows node-to-node. Tool nodes write untrusted content —
     web scrapes, retrieved docs, API responses — directly into state.
     StateGuard scans ONLY the node's return dict (the partial state update),
     not the full state. This is ~80% cheaper and avoids double-scanning.

  2. Supervisor routing hijack (S1.3 + CP.9)
     state["next"] controls graph execution flow. An injection that rewrites
     this key redirects the entire graph. RoutingGuard validates the routing
     key against the declared node inventory before any edge fires.

  3. Subgraph delegation depth (CP.9)
     LangGraph subgraphs are the canonical pattern for spawning child agents.
     CP.9 enforces a delegation depth ceiling:
       ACT-3: max 2 hops  |  ACT-4: max 3 hops  |  ACT-2: max 5 hops

CONTROLS:
  P1.T1.2  — Node return value injection scan
  P1.T1.5  — Credential scan on node output
  P1.T1.10 — State diff scanning (node return = the diff; no full-state scan)
  P1.T2.3  — URL/domain values in state updates
  S1.3     — Routing key validation against declared node inventory
  S1.5     — State write governance (checkpointer write gate)
  F3.2     — Node execution ceiling (across all nodes, all sessions)
  F3.5     — Node error cascade containment
  A2.5     — Per-node OCSF 1.1 trace with state diff hash
  M4.5     — Per-node loop detection (same node N× in session)
  P2.T3.6  — Compliance report
  CP.3     — ACT Capability Tiers 1-4
  CP.4     — NHI registration
  CP.9     — Subgraph replication governance (delegation depth)
  CP.10    — HEAR gate on Class-H patterns in node outputs

All control IDs verified from github.com/CyberStrategyInstitute/ai-safe2-framework

Author: Cyber Strategy Institute — cyberstrategyinstitute.com
License: MIT
"""

from __future__ import annotations

import functools
import json
import uuid
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Set

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.state import CompiledStateGraph
    _LANGGRAPH_AVAILABLE = True
    _END_NODE = END
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    _END_NODE = "__end__"

from enforcement.ai_safe2_engine import (
    AISAFE2Engine,
    AISAFE2Violation,
    AISAFE2ClassHAction,
    CircuitTripped,
    ACTTier,
)

# CP.9 — Maximum subgraph delegation depth by ACT tier
_CP9_MAX_DEPTH: Dict[ACTTier, int] = {
    ACTTier.ACT1: 10,
    ACTTier.ACT2: 5,
    ACTTier.ACT3: 2,
    ACTTier.ACT4: 3,
}

# Minimum string length to scan — avoids scanning short routing tokens, "true", IDs
_MIN_SCAN_LENGTH = 20


# ---------------------------------------------------------------------------
# StateGuard — P1.T1.10 diff-based state scanning
# ---------------------------------------------------------------------------

class StateGuard:
    """
    P1.T1.10 — Indirect Injection Surface Coverage for LangGraph state.

    Scans ONLY the partial state update returned by each node (the diff).
    Never scans the full state dict — that would re-scan already-verified values
    and is O(n) on every node transition.

    Key principle: a node's return value IS the diff. No diffing required.
    The full state is built by LangGraph merging successive partial updates.
    """

    def __init__(self, engine: AISAFE2Engine) -> None:
        self.engine = engine

    def extract_strings(self, value: Any, max_depth: int = 3) -> List[str]:
        """Recursively extract string values from dicts/lists for scanning."""
        if max_depth <= 0:
            return []
        results = []
        if isinstance(value, str):
            results.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                results.extend(self.extract_strings(v, max_depth - 1))
        elif isinstance(value, (list, tuple)):
            for item in value:
                results.extend(self.extract_strings(item, max_depth - 1))
        return results

    def scan_state_update(
        self,
        state_update: Dict[str, Any],
        node_name: str,
        run_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        P1.T1.10 + P1.T1.5 — Scan a node's partial state update.

        Extracts all string values from the update dict (recursively),
        skips values shorter than _MIN_SCAN_LENGTH (routing tokens, IDs, etc.),
        and scans for both injection patterns and credential patterns.

        Returns a violation dict if anything detected, else None.
        """
        all_violations = []

        for key, value in state_update.items():
            strings_to_scan = self.extract_strings(value)
            for text in strings_to_scan:
                if len(text) < _MIN_SCAN_LENGTH:
                    continue
                violation = self.engine.scan_content(
                    text,
                    f"state_update:{node_name}:{key}",
                    check_injection=True,
                    check_credentials=True,
                    run_id=run_id,
                )
                if violation:
                    all_violations.append({"key": key, "violation": violation})

        if all_violations:
            return {"node": node_name, "violations": all_violations}
        return None

    def hash_update(self, state_update: Dict[str, Any]) -> str:
        """A2.5 — Compute a deterministic hash of the state update for audit trail."""
        import hashlib
        try:
            canonical = json.dumps(state_update, sort_keys=True, default=str)
        except Exception:
            canonical = str(state_update)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# RoutingGuard — S1.3 + CP.9 routing key protection
# ---------------------------------------------------------------------------

class RoutingGuard:
    """
    S1.3 + CP.9 — Protect the supervisor routing key (state["next"] or similar)
    from injection and from undeclared routing targets.

    The routing key is high-value: injecting a value here redirects the entire
    graph execution to an arbitrary node. This is the LangGraph equivalent of
    an AgentExecutor tool selection hijack.
    """

    def __init__(
        self,
        engine: AISAFE2Engine,
        declared_nodes: List[str],
    ) -> None:
        self.engine = engine
        # Always include terminal nodes
        self.declared_nodes: Set[str] = set(declared_nodes) | {
            _END_NODE, "__end__", "END", "FINISH",
        }

    def validate(
        self,
        routing_value: str,
        from_node: str,
        run_id: Optional[str] = None,
    ) -> None:
        """
        Validate the routing key value.

        Two checks:
        1. Injection scan — routing value must not contain injection patterns
        2. Node inventory — routing value must be a declared node
        """
        if not routing_value or not isinstance(routing_value, str):
            return

        # P1.T1.2 / S1.3: injection in routing value
        if len(routing_value) >= _MIN_SCAN_LENGTH:
            violation = self.engine.scan_content(
                routing_value,
                f"routing_key:{from_node}",
                check_injection=True,
                check_credentials=False,
                run_id=run_id,
            )
            if violation:
                self.engine._emit_event(
                    "ROUTING_INJECTION_BLOCKED", "CRITICAL", "S1.3",
                    f"routing:{from_node}→{routing_value[:40]}",
                    f"S1.3 Routing injection: injection pattern in routing key from '{from_node}'",
                    run_id,
                )
                if self.engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² S1.3] Routing injection from '{from_node}': "
                        f"injection in routing key value",
                        control_id="S1.3",
                    )

        # CP.9 / S1.3: undeclared routing target
        if self.declared_nodes and routing_value not in self.declared_nodes:
            self.engine._emit_event(
                "ROUTING_HIJACK_ATTEMPT", "CRITICAL", "S1.3",
                f"routing:{from_node}→{routing_value}",
                f"S1.3 Routing hijack: target '{routing_value}' not in declared node inventory "
                f"{sorted(self.declared_nodes)}",
                run_id,
            )
            if self.engine.act_tier.value >= 3:
                raise AISAFE2Violation(
                    f"[AI SAFE² S1.3] Routing target '{routing_value}' not in "
                    f"declared node inventory",
                    control_id="S1.3",
                )


# ---------------------------------------------------------------------------
# SovereignStateGraph — main integration class
# ---------------------------------------------------------------------------

class SovereignStateGraph:
    """
    AI SAFE² v3.0 sovereign enforcement for LangGraph StateGraph.

    Usage — wrap nodes before adding to graph:
        sovereign = SovereignStateGraph(act_tier=ACTTier.ACT3)
        graph = StateGraph(MyState)
        graph.add_node("researcher", sovereign.wrap_node("researcher", researcher_fn))
        graph.add_node("writer", sovereign.wrap_node("writer", writer_fn))
        compiled = graph.compile()
        result = compiled.invoke({"input": "..."})

    For NEXUS mesh (shared engine across all frameworks):
        from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier
        shared_engine = AISAFE2Engine(act_tier=ACTTier.ACT3)
        sovereign = SovereignStateGraph(engine=shared_engine)

    Args:
        engine:              Shared AISAFE2Engine. Created internally if not provided.
        act_tier:            CP.3 ACT tier. Governs fail-open vs fail-closed.
        routing_key:         State key used for supervisor routing. Default "next".
        declared_nodes:      CP.9 + S1.3: exhaustive list of valid node names.
        max_node_calls:      M4.5: per-node execution ceiling within a session.
        max_delegation_depth:CP.9: override default delegation depth for this tier.
        audit_log_dir:       A2.5: directory for OCSF audit logs.
        allowed_domains:     P1.T2.3: outbound domain allowlist for URL state values.
    """

    def __init__(
        self,
        engine: Optional[AISAFE2Engine] = None,
        act_tier: ACTTier = ACTTier.ACT2,
        routing_key: str = "next",
        declared_nodes: Optional[List[str]] = None,
        max_node_calls: int = 10,
        max_delegation_depth: Optional[int] = None,
        audit_log_dir: Optional[Any] = None,
        allowed_domains: Optional[List[str]] = None,
        max_tool_calls: int = 50,
        max_identical_calls: int = 4,
    ) -> None:
        self.engine = engine or AISAFE2Engine(
            runtime_id="langgraph-sovereign-runtime",
            act_tier=act_tier,
            allowed_domains=allowed_domains or [],
            audit_log_dir=audit_log_dir,
            max_tool_calls=max_tool_calls,
            max_identical_calls=max_identical_calls,
        )
        self.routing_key = routing_key
        self.declared_nodes: List[str] = declared_nodes or []
        self.max_node_calls = max_node_calls
        self.max_delegation_depth = (
            max_delegation_depth or _CP9_MAX_DEPTH.get(self.engine.act_tier, 2)
        )

        # Per-session state
        self._node_call_counts: Dict[str, int] = defaultdict(int)
        self._delegation_depth: int = 0

        # Sub-components
        self.state_guard = StateGuard(self.engine)
        self.routing_guard = RoutingGuard(self.engine, self.declared_nodes)

    # -----------------------------------------------------------------------
    # Core: wrap_node — the primary integration point
    # -----------------------------------------------------------------------

    def wrap_node(self, node_name: str, node_fn: Callable) -> Callable:
        """
        Wrap a LangGraph node function with AI SAFE² enforcement.

        The wrapped function:
          1. Records the node execution for F3.2 ceiling and M4.5 loop detection
          2. Executes the original node function
          3. Scans the partial state update for P1.T1.10 injection + P1.T1.5 credentials
          4. Validates the routing key for S1.3 + CP.9 (if routing_key present in update)
          5. Checks HEAR gate for CP.10 on any Class-H patterns in update
          6. Logs an OCSF audit event with the state update hash (A2.5)

        Raises: AISAFE2Violation, CircuitTripped, AISAFE2ClassHAction (ACT-3+)
        """
        sovereign = self
        engine = self.engine
        state_guard = self.state_guard
        routing_guard = self.routing_guard

        @functools.wraps(node_fn)
        def _sovereign_node(state: Any, *args: Any, **kwargs: Any) -> Any:
            run_id = str(uuid.uuid4())

            # ── M4.5: per-node loop detection ─────────────────────────────
            sovereign._node_call_counts[node_name] += 1
            call_count = sovereign._node_call_counts[node_name]
            if call_count > sovereign.max_node_calls:
                engine._emit_event(
                    "NODE_LOOP_DETECTED", "CRITICAL", "M4.5",
                    f"node:{node_name}",
                    f"M4.5 Node loop: '{node_name}' executed {call_count}× in session "
                    f"(ceiling: {sovereign.max_node_calls})",
                    run_id,
                )
                if engine.act_tier.value >= 2:
                    raise CircuitTripped(
                        f"[AI SAFE² M4.5] Node loop: '{node_name}' called {call_count}×",
                        control_id="M4.5",
                    )

            # ── F3.2: global node execution ceiling ───────────────────────
            try:
                engine.record_tool_call(f"node:{node_name}", node_name)
            except CircuitTripped:
                raise

            # ── F3.4: snapshot state before execution ─────────────────────
            state_dict: Dict = state if isinstance(state, dict) else {}
            engine.snapshot_state(state_dict, label=f"pre:{node_name}")

            # ── Execute the wrapped node ───────────────────────────────────
            try:
                result = node_fn(state, *args, **kwargs)
            except (AISAFE2Violation, CircuitTripped, AISAFE2ClassHAction):
                raise
            except Exception as e:
                # F3.5: contain node errors
                try:
                    engine.record_chain_error(e, node_name, run_id=run_id)
                except CircuitTripped:
                    raise
                raise

            # ── Post-execution enforcement ─────────────────────────────────
            if result and isinstance(result, dict):

                # P1.T1.10 + P1.T1.5: scan the partial state update
                violation = state_guard.scan_state_update(result, node_name, run_id)
                if violation and engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.10] Injection in state update from node "
                        f"'{node_name}'",
                        control_id="P1.T1.10",
                    )

                # S1.3 + CP.9: validate routing key
                if sovereign.routing_key in result and sovereign.declared_nodes:
                    routing_guard.validate(
                        str(result[sovereign.routing_key]),
                        node_name,
                        run_id,
                    )

                # P1.T2.3: check URL values in state update
                for key, value in result.items():
                    if isinstance(value, str) and (
                        value.startswith("http://") or value.startswith("https://")
                    ):
                        try:
                            engine.check_domain(value, run_id=run_id)
                        except AISAFE2Violation:
                            if engine.act_tier.value >= 3:
                                raise

                # CP.10: HEAR gate on Class-H patterns
                if engine.hear_mode:
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) >= _MIN_SCAN_LENGTH:
                            engine.check_hear_gate(value, run_id=run_id)

                # A2.5: emit node completion event with state update hash
                update_hash = state_guard.hash_update(result)
                engine._emit_event(
                    "NODE_COMPLETED", "INFO", "A2.5",
                    f"node:{node_name}",
                    f"A2.5 Node '{node_name}' completed — update hash: {update_hash} "
                    f"(keys: {list(result.keys())})",
                    run_id,
                )

            return result

        return _sovereign_node

    # -----------------------------------------------------------------------
    # CP.9 — Subgraph delegation depth
    # -----------------------------------------------------------------------

    def enter_subgraph(
        self,
        subgraph_name: str = "",
        run_id: Optional[str] = None,
    ) -> None:
        """
        CP.9 — Call before invoking a subgraph (child agent).
        Increments delegation depth and raises CircuitTripped if limit exceeded.

        Pattern:
            sovereign.enter_subgraph("research-subgraph")
            try:
                result = subgraph.invoke(state)
            finally:
                sovereign.exit_subgraph()
        """
        self._delegation_depth += 1
        if self._delegation_depth > self.max_delegation_depth:
            self.engine._emit_event(
                "CP9_DELEGATION_EXCEEDED", "CRITICAL", "CP.9",
                f"subgraph:{subgraph_name}",
                f"CP.9 Delegation depth {self._delegation_depth} exceeds "
                f"ACT-{self.engine.act_tier.value} limit {self.max_delegation_depth}",
                run_id,
            )
            self._delegation_depth -= 1  # rollback before raising
            raise CircuitTripped(
                f"[AI SAFE² CP.9] Subgraph delegation depth "
                f"{self._delegation_depth + 1} exceeds "
                f"ACT-{self.engine.act_tier.value} limit {self.max_delegation_depth}",
                control_id="CP.9",
            )
        self.engine._emit_event(
            "SUBGRAPH_ENTERED", "INFO", "CP.9",
            f"subgraph:{subgraph_name}",
            f"CP.9 Subgraph entered: '{subgraph_name}' "
            f"(depth: {self._delegation_depth}/{self.max_delegation_depth})",
            run_id,
        )

    def exit_subgraph(self, subgraph_name: str = "") -> None:
        """CP.9 — Call after subgraph completion (success or failure)."""
        self._delegation_depth = max(0, self._delegation_depth - 1)

    # -----------------------------------------------------------------------
    # S1.5 — State write governance (checkpointer gate)
    # -----------------------------------------------------------------------

    def protect_state_write(
        self,
        state_update: Dict[str, Any],
        source_node: str = "unknown",
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        S1.5 — Gate state writes intended for persistence (checkpointer, external store).

        Call this before writing state to a LangGraph checkpointer, Redis,
        Postgres, or any external persistence layer.

        Validates each string value via protect_memory_write() — same gate as
        LangChain's ConversationBufferMemory.
        """
        for key, value in state_update.items():
            if isinstance(value, str) and len(value) >= _MIN_SCAN_LENGTH:
                self.engine.protect_memory_write(key, value, run_id=run_id)
        return state_update

    # -----------------------------------------------------------------------
    # Async wrapper — sync-first; async wrappers available on request
    # -----------------------------------------------------------------------

    def wrap_node_async(self, node_name: str, node_fn: Callable) -> Callable:
        """
        Async variant of wrap_node for use with graph.astream() / graph.ainvoke().
        The enforcement logic is identical — same controls, same exceptions.
        """
        sovereign = self
        sync_wrapped = self.wrap_node(node_name, node_fn)

        async def _async_sovereign_node(state: Any, *args: Any, **kwargs: Any) -> Any:
            # Run the sync enforcement wrapper in a thread pool to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: sync_wrapped(state, *args, **kwargs)
            )

        functools.update_wrapper(_async_sovereign_node, node_fn)
        return _async_sovereign_node

    # -----------------------------------------------------------------------
    # Convenience
    # -----------------------------------------------------------------------

    def get_status(self) -> Dict:
        """Return combined enforcement + delegation status."""
        status = self.engine.get_status()
        status["langgraph_specific"] = {
            "delegation_depth": self._delegation_depth,
            "max_delegation_depth": self.max_delegation_depth,
            "routing_key": self.routing_key,
            "declared_nodes": self.declared_nodes,
            "node_call_counts": dict(self._node_call_counts),
        }
        return status

    def compliance_report(self) -> str:
        return self.engine.compliance_report()
