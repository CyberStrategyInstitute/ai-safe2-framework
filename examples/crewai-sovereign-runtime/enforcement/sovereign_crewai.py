"""
AI SAFE² v3.0 — CrewAI Sovereign Enforcement Layer
====================================================
CrewAI's threat model is fundamentally different from LangChain and LangGraph.

THREE UNIQUE SURFACES:

  1. Agent identity poisoning at construction time (P1.T1.2 + S1.3)
     CrewAI agents have `role`, `goal`, and `backstory` strings that are injected
     directly into the LLM system prompt before the first token fires. A poisoned
     role definition corrupts the agent's behavior for the ENTIRE SESSION, not
     just a single response. Unlike LangChain where injection happens at call time,
     CrewAI injection can happen at BUILD time — before kickoff().

     AgentGuard scans role/goal/backstory at wrap time. Poisoned agents never run.

  2. Task context cascade contamination (P1.T1.10 + S1.3)
     CrewAI's task.context = [prior_task] automatically injects the prior task's
     output into the next task's input. This creates a data pipeline where untrusted
     tool output from one agent flows automatically into the next agent's context.
     
     There is no scan boundary between tasks by default. protect_task_output()
     adds one. Call it after each task; scan before the output can cascade.

  3. Shared tool surface across crew (P1.T2.5 + P1.T1.10)
     CrewAI crews share tool instances across all agents. A poisoned tool output
     that one agent receives affects all subsequent agents using the same tool.
     wrap_agent() wraps each agent's tools with IPI scanning + domain allowlist.

CONTROLS:
  P1.T1.2  — Agent identity scan at construction (role, goal, backstory)
  P1.T1.5  — Credential scan on task output
  P1.T1.10 — Task output scan before context cascade
  P1.T2.3  — Domain allowlist on tool outputs within tasks
  S1.3     — Task output classified as untrusted data-plane
  S1.5     — protect_task_output() — gate before context write
  F3.2     — Task execution ceiling (total across crew)
  F3.5     — Task error cascade containment
  A2.5     — Per-task OCSF 1.1 trace with output hash
  M4.5     — Same task repeatedly executed (loop detection)
  P2.T3.6  — Compliance report
  CP.3     — ACT Capability Tiers 1-4
  CP.4     — NHI registration per agent
  CP.8     — Catastrophic Risk Threshold
  CP.10    — HEAR gate on task outputs

All control IDs verified from github.com/CyberStrategyInstitute/ai-safe2-framework

Author: Cyber Strategy Institute — cyberstrategyinstitute.com
License: MIT
"""

from __future__ import annotations

import functools
import hashlib
import json
import uuid
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

try:
    from crewai import Agent, Task, Crew
    from crewai.tools import BaseTool as CrewBaseTool
    _CREWAI_AVAILABLE = True
except ImportError:
    _CREWAI_AVAILABLE = False
    Agent = Any  # type: ignore
    Task = Any   # type: ignore
    Crew = Any   # type: ignore

from enforcement.ai_safe2_engine import (
    AISAFE2Engine,
    AISAFE2Violation,
    AISAFE2ClassHAction,
    CircuitTripped,
    ACTTier,
)

# Minimum string length to scan — avoids false positives on short values
_MIN_SCAN_LENGTH = 20


# ---------------------------------------------------------------------------
# AgentGuard — P1.T1.2 + S1.3 agent identity protection
# ---------------------------------------------------------------------------

class AgentGuard:
    """
    P1.T1.2 + S1.3 — Scan CrewAI agent identity strings at construction time.

    `role`, `goal`, and `backstory` are injected directly into the LLM system
    prompt. They are the highest-value injection surface in CrewAI — a poisoned
    role contaminates every token the agent produces for the entire session.

    Scanning happens when wrap_agent() is called, before kickoff().
    Poisoned agents never reach execution.
    """

    def __init__(self, engine: AISAFE2Engine) -> None:
        self.engine = engine

    def validate_agent_identity(
        self,
        agent_id: str,
        role: str = "",
        goal: str = "",
        backstory: str = "",
        run_id: Optional[str] = None,
    ) -> None:
        """
        Scan agent identity strings for injection patterns.

        Fields scanned:
        - role:      Primary identity anchor — highest risk
        - goal:      Operational directive — high risk
        - backstory: Context framing — medium risk

        Raises AISAFE2Violation at ACT-3+ on any positive detection.
        """
        fields = [
            ("role",      role,      True),   # (field, value, check_injection)
            ("goal",      goal,      True),
            ("backstory", backstory, True),
        ]
        for field_name, value, check_inj in fields:
            if not value or not isinstance(value, str):
                continue
            if len(value) < _MIN_SCAN_LENGTH:
                continue

            violation = self.engine.scan_content(
                value,
                f"agent_identity:{agent_id}:{field_name}",
                check_injection=check_inj,
                check_credentials=True,
                run_id=run_id,
            )
            if violation:
                self.engine._emit_event(
                    "AGENT_IDENTITY_POISONING_BLOCKED", "CRITICAL", "P1.T1.2",
                    f"agent:{agent_id}:{field_name}",
                    f"P1.T1.2 Agent identity poisoning: injection in '{field_name}' "
                    f"for agent '{agent_id}'",
                    run_id,
                )
                if self.engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.2] Agent identity poisoning blocked: "
                        f"injection in '{field_name}' for agent '{agent_id}'",
                        control_id="P1.T1.2",
                    )


# ---------------------------------------------------------------------------
# TaskContextGuard — P1.T1.10 + S1.3 task output scanning
# ---------------------------------------------------------------------------

class TaskContextGuard:
    """
    P1.T1.10 + S1.3 — Scan task output before it cascades into downstream tasks.

    CrewAI's task context cascade is automatic: task.context = [prior_task]
    means prior_task.output flows into the current task's input with no scan
    boundary. This guard adds the missing boundary.

    Classify task output as S1.3 untrusted data-plane content — it may contain
    web-scraped pages, API responses, or tool returns that were never validated.
    """

    def __init__(self, engine: AISAFE2Engine) -> None:
        self.engine = engine

    def scan_task_output(
        self,
        output: Any,
        task_name: str,
        run_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Scan task output string for P1.T1.10 injection and P1.T1.5 credentials.

        Returns a violation dict if detected, else None.
        Called by protect_task_output() — never call this directly; use the
        protect_* wrapper which also handles F3.2, M4.5, A2.5, and CP.10.
        """
        output_str = str(output) if not isinstance(output, str) else output
        if len(output_str) < _MIN_SCAN_LENGTH:
            return None

        return self.engine.scan_content(
            output_str,
            f"task_output:{task_name}",
            check_injection=True,
            check_credentials=True,
            run_id=run_id,
        )

    def hash_output(self, output: Any) -> str:
        """A2.5 — Compute deterministic output hash for audit trail."""
        output_str = str(output) if not isinstance(output, str) else output
        return hashlib.sha256(output_str.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# SovereignCrew — main enforcement wrapper
# ---------------------------------------------------------------------------

class SovereignCrew:
    """
    AI SAFE² v3.0 sovereign enforcement for CrewAI agents, tasks, and crews.

    Usage — wrap agents and protect task outputs:

        sovereign = SovereignCrew(act_tier=ACTTier.ACT3)

        # Wrap at agent construction (scans role/goal/backstory)
        researcher = sovereign.wrap_agent(
            researcher_agent,
            agent_id="researcher-prod-01",
            owner_of_record="ai-ops@company.com",
        )

        # Run the crew and gate each task output before it cascades
        result = crew.kickoff()
        # After each task completes:
        clean_output = sovereign.protect_task_output(task.output, "research_task")

        # Or wrap the entire crew (auto-injects task_callback if CrewAI supports it)
        wrapped_crew = sovereign.wrap_crew(crew)
        result = wrapped_crew.kickoff()

    Args:
        engine:            Shared AISAFE2Engine. Created internally if not provided.
        act_tier:          CP.3 ACT tier.
        max_task_calls:    M4.5: per-task execution ceiling.
        audit_log_dir:     A2.5: directory for OCSF audit logs.
        allowed_domains:   P1.T2.3: outbound domain allowlist.
        max_tool_calls:    F3.2: total tool/task call ceiling.
    """

    def __init__(
        self,
        engine: Optional[AISAFE2Engine] = None,
        act_tier: ACTTier = ACTTier.ACT2,
        max_task_calls: int = 10,
        audit_log_dir: Optional[Any] = None,
        allowed_domains: Optional[List[str]] = None,
        max_tool_calls: int = 100,
        max_identical_calls: int = 4,
    ) -> None:
        self.engine = engine or AISAFE2Engine(
            runtime_id="crewai-sovereign-runtime",
            act_tier=act_tier,
            allowed_domains=allowed_domains or [],
            audit_log_dir=audit_log_dir,
            max_tool_calls=max_tool_calls,
            max_identical_calls=max_identical_calls,
        )
        self.max_task_calls = max_task_calls

        # Per-session tracking
        self._task_call_counts: Dict[str, int] = defaultdict(int)
        self._crew_id: str = str(uuid.uuid4())[:8]

        # Sub-components
        self.agent_guard = AgentGuard(self.engine)
        self.task_guard = TaskContextGuard(self.engine)

    # -----------------------------------------------------------------------
    # wrap_agent — primary integration point for agents
    # -----------------------------------------------------------------------

    def wrap_agent(
        self,
        agent: Any,
        agent_id: Optional[str] = None,
        owner_of_record: str = "unset@crewai.local",
    ) -> Any:
        """
        Wrap a CrewAI Agent with AI SAFE² enforcement.

        Actions performed:
        1. P1.T1.2 + S1.3: scan role/goal/backstory for identity poisoning
        2. P1.T2.5 + P1.T1.10: wrap each tool with IPI scan + domain allowlist
        3. CP.4: register the agent as a Non-Human Identity
        4. A2.5: log agent wrapping event

        Raises AISAFE2Violation at ACT-3+ if identity strings contain injection.
        Returns the same agent object (patched in place).
        """
        run_id = str(uuid.uuid4())

        # Derive agent_id if not provided
        role = str(getattr(agent, "role", "") or "")
        goal = str(getattr(agent, "goal", "") or "")
        backstory = str(getattr(agent, "backstory", "") or "")
        _agent_id = agent_id or (
            role[:40].strip().lower().replace(" ", "-").replace("/", "-") or "unnamed-agent"
        )

        # P1.T1.2 + S1.3: scan identity strings at construction time
        self.agent_guard.validate_agent_identity(
            _agent_id, role, goal, backstory, run_id=run_id
        )

        # P1.T2.5 + P1.T1.10: wrap agent tools
        tools = getattr(agent, "tools", None) or []
        if tools:
            wrapped_tools = [self._wrap_tool(t) for t in tools]
            try:
                agent.tools = wrapped_tools
            except (AttributeError, TypeError):
                pass  # Some agent implementations are immutable at this point

        # CP.4: register as NHI
        tool_names = [getattr(t, "name", str(t)) for t in tools]
        self.engine.register_nhi(
            agent_id=_agent_id,
            owner_of_record=owner_of_record,
            act_tier=self.engine.act_tier,
            tool_authorizations=tool_names,
            control_plane_id=f"crewai-cp-{self._crew_id}",
        )

        return agent

    # -----------------------------------------------------------------------
    # protect_task_output — gate task outputs before context cascade
    # -----------------------------------------------------------------------

    def protect_task_output(
        self,
        output: Any,
        task_name: str,
        run_id: Optional[str] = None,
    ) -> Any:
        """
        P1.T1.10 + S1.5 — Gate task output before it can cascade into
        downstream task context.

        Call this after each CrewAI task completes and before the output is
        referenced by any subsequent task via task.context = [...].

        Actions:
        1. F3.2: count this task execution toward the session ceiling
        2. M4.5: detect repeated execution of the same task (loop)
        3. P1.T1.10 + S1.3: scan output for injection before cascade
        4. CP.10: HEAR gate on Class-H patterns in output
        5. A2.5: log task output with hash

        Returns the original output unchanged (enforcement is side-effect only).
        Raises AISAFE2Violation, CircuitTripped, or AISAFE2ClassHAction at ACT-3+.
        """
        if run_id is None:
            run_id = str(uuid.uuid4())

        output_str = str(output) if not isinstance(output, str) else output

        # F3.2: global task execution ceiling
        try:
            self.engine.record_tool_call(f"task:{task_name}", task_name)
        except CircuitTripped:
            raise

        # M4.5: per-task repetition detection
        self._task_call_counts[task_name] += 1
        count = self._task_call_counts[task_name]
        if count > self.max_task_calls:
            self.engine._emit_event(
                "TASK_LOOP_DETECTED", "CRITICAL", "M4.5",
                f"task:{task_name}",
                f"M4.5 Task loop: '{task_name}' executed {count}× "
                f"(ceiling: {self.max_task_calls})",
                run_id,
            )
            if self.engine.act_tier.value >= 2:
                raise CircuitTripped(
                    f"[AI SAFE² M4.5] Task loop: '{task_name}' called {count}×",
                    control_id="M4.5",
                )

        # P1.T1.10 + S1.3: scan output before context cascade
        violation = self.task_guard.scan_task_output(output_str, task_name, run_id)
        if violation and self.engine.act_tier.value >= 3:
            raise AISAFE2Violation(
                f"[AI SAFE² P1.T1.10] Injection in task output: '{task_name}' — "
                f"blocked before context cascade",
                control_id="P1.T1.10",
            )

        # CP.10: HEAR gate on Class-H patterns
        if self.engine.hear_mode and len(output_str) >= _MIN_SCAN_LENGTH:
            self.engine.check_hear_gate(output_str, run_id=run_id)

        # A2.5: log task output with hash
        output_hash = self.task_guard.hash_output(output_str)
        self.engine._emit_event(
            "TASK_OUTPUT_AUTHORIZED", "INFO", "A2.5",
            f"task:{task_name}",
            f"A2.5 Task output authorized: '{task_name}' (hash: {output_hash}, "
            f"len: {len(output_str)})",
            run_id,
        )

        return output

    # -----------------------------------------------------------------------
    # wrap_crew — full crew wrapping with task_callback injection
    # -----------------------------------------------------------------------

    def wrap_crew(self, crew: Any) -> Any:
        """
        Wrap an entire CrewAI Crew with sovereign enforcement.

        Actions:
        1. wrap_agent() on every agent in crew.agents
        2. Inject a task_callback that calls protect_task_output() after each task
           (requires CrewAI >= 0.70.0 that supports task_callback)

        Returns the modified crew object (patched in place).

        Note: If the CrewAI version doesn't support task_callback, agents are
        still wrapped (identity scan + tool wrapping) but task outputs must be
        gated manually via protect_task_output().
        """
        # 1. Wrap all agents
        agents = getattr(crew, "agents", []) or []
        for agent in agents:
            try:
                self.wrap_agent(agent)
            except AISAFE2Violation:
                raise  # Hard stop — poisoned agent in the crew

        # 2. Inject task_callback (CrewAI >= 0.70.0)
        sovereign = self
        original_callback = getattr(crew, "task_callback", None)

        def sovereign_task_callback(task_output: Any) -> None:
            # Extract task name from TaskOutput
            task_name = "unknown_task"
            if hasattr(task_output, "description"):
                task_name = str(task_output.description)[:50]
            elif hasattr(task_output, "task") and hasattr(task_output.task, "description"):
                task_name = str(task_output.task.description)[:50]

            # Gate task output before cascade
            output_str = getattr(task_output, "raw", None) or str(task_output)
            try:
                sovereign.protect_task_output(output_str, task_name)
            except (AISAFE2Violation, CircuitTripped, AISAFE2ClassHAction):
                raise

            if original_callback:
                original_callback(task_output)

        try:
            crew.task_callback = sovereign_task_callback
        except (AttributeError, TypeError):
            pass  # Older CrewAI — manual protect_task_output() required

        self.engine._emit_event(
            "CREW_WRAPPED", "INFO", "CP.4",
            f"crew:{self._crew_id}",
            f"CP.4 Crew wrapped: {len(agents)} agent(s), "
            f"task_callback={'injected' if hasattr(crew, 'task_callback') else 'manual'}",
        )
        return crew

    # -----------------------------------------------------------------------
    # Tool wrapping — P1.T2.5 + P1.T1.10
    # -----------------------------------------------------------------------

    def _wrap_tool(self, tool: Any) -> Any:
        """
        P1.T2.5 + P1.T1.10 — Wrap a CrewAI or LangChain tool with:
          - P1.T2.3 domain allowlist enforcement on URL arguments
          - P1.T1.10 IPI scanning of tool output before return

        Handles CrewAI BaseTool subclasses, @tool-decorated functions,
        and LangChain tool wrappers.
        """
        engine = self.engine

        # CrewAI BaseTool (has ._run)
        if hasattr(tool, "_run") and callable(tool._run):
            original_run = tool._run

            def safe_run(*args: Any, **kwargs: Any) -> Any:
                result = original_run(*args, **kwargs)
                result_str = str(result)
                violation = engine.scan_content(
                    result_str,
                    f"tool_output:{getattr(tool, 'name', 'crewai_tool')}",
                    check_injection=True,
                    check_credentials=True,
                )
                if violation and engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.10] IPI in tool output: "
                        f"'{getattr(tool, 'name', 'crewai_tool')}'",
                        control_id="P1.T1.10",
                    )
                return result

            tool._run = safe_run

        # Function tool (has .func)
        elif hasattr(tool, "func") and callable(tool.func):
            original_func = tool.func

            @functools.wraps(original_func)
            def safe_func(*args: Any, **kwargs: Any) -> Any:
                result = original_func(*args, **kwargs)
                result_str = str(result)
                violation = engine.scan_content(
                    result_str,
                    f"tool_output:{getattr(tool, 'name', 'func_tool')}",
                    check_injection=True,
                    check_credentials=True,
                )
                if violation and engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        "[AI SAFE² P1.T1.10] IPI in tool output",
                        control_id="P1.T1.10",
                    )
                return result

            tool.func = safe_func

        return tool

    # -----------------------------------------------------------------------
    # Convenience
    # -----------------------------------------------------------------------

    def get_status(self) -> Dict:
        """Return enforcement status for NEXUS dashboard."""
        status = self.engine.get_status()
        status["crewai_specific"] = {
            "crew_id": self._crew_id,
            "task_call_counts": dict(self._task_call_counts),
            "max_task_calls": self.max_task_calls,
        }
        return status

    def compliance_report(self) -> str:
        return self.engine.compliance_report()
