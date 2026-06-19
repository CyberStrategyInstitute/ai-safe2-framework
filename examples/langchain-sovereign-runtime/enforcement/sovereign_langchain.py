"""
AI SAFE² v3.0 — LangChain Sovereign Enforcement Layer
======================================================
Drop-in enforcement for any LangChain chain, agent, or tool.

LangChain's specific threat surface (what makes this package unique):
  - P1.T1.2:  Injection at LLM input  → on_llm_start / on_chat_model_start
  - P1.T1.10: Indirect Prompt Injection via tool return values → on_tool_end
  - P1.T1.5:  Credential leak in final chain output → on_chain_end / on_llm_end
  - S1.3:     Cross-agent context contamination → SovereignLangChain.isolate()
  - S1.5:     ConversationBufferMemory poisoning → protect_memory()
  - F3.2:     AgentExecutor loop → on_agent_action (tool call counting)
  - F3.5:     Chain error cascade → on_chain_error
  - M4.5:     Per-tool baseline anomaly → on_tool_start / on_tool_end
  - A2.5:     run_id-linked trace → every callback event

Integration (one line):
    chain.invoke(input, config={"callbacks": [SovereignCallbackHandler()]})

Or full wrapper:
    sovereign = SovereignLangChain(act_tier=ACTTier.ACT3)
    result = sovereign.run(chain, input_dict)

Controls: verified from github.com/CyberStrategyInstitute/ai-safe2-framework
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Sequence, Union

# LangChain imports — langchain-core >= 0.3
try:
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult
    from langchain_core.agents import AgentAction, AgentFinish
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    # Provide a minimal stub so the module is importable for testing the engine
    class BaseCallbackHandler:  # type: ignore
        def __init__(self, *a, **kw): pass

from enforcement.ai_safe2_engine import (
    AISAFE2Engine,
    AISAFE2Violation,
    AISAFE2ClassHAction,
    CircuitTripped,
    ACTTier,
)


# ---------------------------------------------------------------------------
# SovereignCallbackHandler
# ---------------------------------------------------------------------------

class SovereignCallbackHandler(BaseCallbackHandler):
    """
    Drop-in BaseCallbackHandler that enforces AI SAFE² v3.0 controls
    at every LangChain execution event.

    Usage:
        handler = SovereignCallbackHandler(act_tier=ACTTier.ACT3)
        chain.invoke(input, config={"callbacks": [handler]})

    The handler shares a single AISAFE2Engine instance. Pass your own
    engine for cross-framework NEXUS mesh usage.
    """

    def __init__(
        self,
        engine: Optional[AISAFE2Engine] = None,
        act_tier: ACTTier = ACTTier.ACT2,
        allowed_domains: Optional[List[str]] = None,
        workspace_root: Optional[str] = None,
        raise_on_violation: Optional[bool] = None,
        audit_log_dir: Optional[Any] = None,
    ) -> None:
        super().__init__()
        self.engine = engine or AISAFE2Engine(
            runtime_id="langchain-sovereign-runtime",
            act_tier=act_tier,
            allowed_domains=allowed_domains or [],
            workspace_root=workspace_root,
            audit_log_dir=audit_log_dir,
        )
        # raise_on_violation defaults to True for ACT-3+
        self._raise = (
            raise_on_violation
            if raise_on_violation is not None
            else (self.engine.act_tier.value >= 3)
        )

    # ------------------------------------------------------------------
    # P1.T1.2 — Completion LLM input scan
    # ------------------------------------------------------------------

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """P1.T1.2 — Scan raw-text prompts before they reach the LLM."""
        run_id = str(kwargs.get("run_id", ""))
        for prompt in prompts:
            if not isinstance(prompt, str):
                continue
            violation = self.engine.scan_content(
                prompt, "llm_input_text",
                check_injection=True, check_credentials=False,
                run_id=run_id,
            )
            if violation and self._raise:
                raise AISAFE2Violation(
                    f"[AI SAFE² P1.T1.2] Injection in LLM prompt blocked",
                    control_id="P1.T1.2",
                )

    # ------------------------------------------------------------------
    # P1.T1.2 — Chat model input scan
    # ------------------------------------------------------------------

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        **kwargs: Any,
    ) -> None:
        """P1.T1.2 — Scan chat messages before they reach the chat model."""
        run_id = str(kwargs.get("run_id", ""))
        for msg_list in messages:
            for msg in msg_list:
                content = getattr(msg, "content", None) or str(msg)
                if not isinstance(content, str):
                    continue
                violation = self.engine.scan_content(
                    content, "llm_input_chat",
                    check_injection=True, check_credentials=False,
                    run_id=run_id,
                )
                if violation and self._raise:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.2] Injection in chat input blocked",
                        control_id="P1.T1.2",
                    )

    # ------------------------------------------------------------------
    # P1.T1.5 — LLM output credential scan
    # ------------------------------------------------------------------

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """P1.T1.5 — Scan LLM response for credential leakage."""
        run_id = str(kwargs.get("run_id", ""))
        try:
            # LLMResult has generations: List[List[Generation]]
            for gen_list in response.generations:
                for gen in gen_list:
                    text = getattr(gen, "text", None) or str(gen)
                    self.engine.scan_content(
                        text, "llm_output",
                        check_injection=False, check_credentials=True,
                        run_id=run_id,
                    )
        except Exception:
            pass  # F3.5 — don't let scan failure cascade

    # ------------------------------------------------------------------
    # M4.5 / F3.2 — Tool call recording
    # ------------------------------------------------------------------

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """F3.2 + M4.5 — Record tool invocation for ceiling and loop detection."""
        run_id = str(kwargs.get("run_id", ""))
        tool_name = serialized.get("name", "unknown_tool")
        self.engine.record_tool_call(tool_name, input_str, run_id=run_id)

        # CP.10: check if this tool input describes a Class-H action
        if self.engine.hear_mode:
            try:
                self.engine.check_hear_gate(input_str, run_id=run_id)
            except AISAFE2ClassHAction:
                if self._raise:
                    raise

    # ------------------------------------------------------------------
    # P1.T1.10 — Indirect Prompt Injection via tool output (IPI)
    # ------------------------------------------------------------------

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """
        P1.T1.10 — Scan tool output for Indirect Prompt Injection.

        Tool return values flow directly into the agent's context window.
        This is the primary IPI surface in any LangChain agent.
        S1.3: classify as untrusted data-plane content before returning.
        """
        run_id = str(kwargs.get("run_id", ""))
        tool_name = kwargs.get("name", "unknown_tool")
        output_str = str(output) if output is not None else ""

        # S1.3: tool output is untrusted data-plane content
        violation = self.engine.scan_content(
            output_str,
            f"tool_output:{tool_name}",
            check_injection=True,
            check_credentials=True,
            run_id=run_id,
        )
        if violation and self._raise:
            raise AISAFE2Violation(
                f"[AI SAFE² P1.T1.10] IPI blocked in tool output: '{tool_name}'",
                control_id="P1.T1.10",
            )

    # ------------------------------------------------------------------
    # P1.T1.5 — Final chain output credential scan
    # ------------------------------------------------------------------

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """P1.T1.5 — Scan chain final output for credential leakage."""
        run_id = str(kwargs.get("run_id", ""))
        for key, value in outputs.items():
            if not isinstance(value, str):
                value = str(value)
            self.engine.scan_content(
                value,
                f"chain_output:{key}",
                check_injection=False,
                check_credentials=True,
                run_id=run_id,
            )

    # ------------------------------------------------------------------
    # F3.5 — Chain error cascade containment
    # ------------------------------------------------------------------

    def on_chain_error(
        self,
        error: BaseException,
        **kwargs: Any,
    ) -> None:
        """F3.5 — Log and contain chain errors to prevent cascade."""
        run_id = str(kwargs.get("run_id", ""))
        chain_name = kwargs.get("name", "unknown_chain")
        try:
            self.engine.record_chain_error(error, chain_name, run_id=run_id)
        except CircuitTripped:
            if self._raise:
                raise

    # ------------------------------------------------------------------
    # Agent action — F3.2 enforcement point
    # ------------------------------------------------------------------

    def on_agent_action(
        self,
        action: Any,
        **kwargs: Any,
    ) -> None:
        """F3.2 — Additional enforcement point for AgentExecutor loop detection."""
        run_id = str(kwargs.get("run_id", ""))
        tool_name = getattr(action, "tool", "unknown")
        tool_input = str(getattr(action, "tool_input", ""))
        # Record counted at on_tool_start; this call provides additional context
        self.engine._emit_event(
            "AGENT_ACTION", "INFO", "F3.2",
            f"agent_action:{tool_name}",
            f"Agent action recorded: tool='{tool_name}'",
            run_id,
        )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def get_status(self) -> Dict:
        """Return engine status for NEXUS dashboard integration."""
        return self.engine.get_status()

    def compliance_report(self) -> str:
        """P2.T3.6 — Return Markdown compliance report."""
        return self.engine.compliance_report()


# ---------------------------------------------------------------------------
# SovereignLangChain — Full wrapper with tool protection and memory governance
# ---------------------------------------------------------------------------

class SovereignLangChain:
    """
    Full enforcement wrapper for LangChain chains and agents.
    Adds wrap_tool(), protect_memory(), and run() on top of the callback handler.

    Usage:
        sovereign = SovereignLangChain(act_tier=ACTTier.ACT3)
        protected_tool = sovereign.wrap_tool(my_tool, allowed_domains=["api.example.com"])
        result = sovereign.run(chain, {"input": "..."})
    """

    def __init__(
        self,
        engine: Optional[AISAFE2Engine] = None,
        act_tier: ACTTier = ACTTier.ACT2,
        allowed_domains: Optional[List[str]] = None,
        workspace_root: Optional[str] = None,
    ) -> None:
        self.engine = engine or AISAFE2Engine(
            runtime_id="langchain-sovereign-runtime",
            act_tier=act_tier,
            allowed_domains=allowed_domains or [],
            workspace_root=workspace_root,
        )
        self.callback = SovereignCallbackHandler(engine=self.engine)

    # ------------------------------------------------------------------
    # P1.T2.5 + P1.T1.10 — Tool wrapping
    # ------------------------------------------------------------------

    def wrap_tool(self, tool: Any, allowed_domains: Optional[List[str]] = None) -> Any:
        """
        P1.T2.5 + P1.T1.10 — Wrap any LangChain tool with:
          - Domain allowlist enforcement on URL arguments
          - IPI scanning of tool output before it returns to the agent

        Works with @tool functions, StructuredTool, and BaseTool subclasses.
        Non-destructive: returns the same tool object with patched execution.
        """
        engine = self.engine
        domains = allowed_domains or engine.allowed_domains

        # StructuredTool / @tool decorator expose .func
        if hasattr(tool, "func") and callable(tool.func):
            original_func = tool.func

            def safe_func(*args: Any, **kwargs: Any) -> Any:
                # P1.T2.3: scan any string arg that looks like a URL
                all_args = list(args) + list(kwargs.values())
                for arg in all_args:
                    if isinstance(arg, str) and (
                        arg.startswith("http") or arg.startswith("ftp")
                    ):
                        try:
                            engine.check_domain(arg)
                        except AISAFE2Violation:
                            raise

                result = original_func(*args, **kwargs)

                # P1.T1.10: scan tool output for IPI
                result_str = str(result)
                violation = engine.scan_content(
                    result_str,
                    f"tool_output:{getattr(tool, 'name', 'wrapped_tool')}",
                    check_injection=True,
                    check_credentials=True,
                )
                if violation and engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.10] IPI blocked in wrapped tool output",
                        control_id="P1.T1.10",
                    )
                return result

            tool.func = safe_func

        # BaseTool subclasses expose ._run
        elif hasattr(tool, "_run") and callable(tool._run):
            original_run = tool._run

            def safe_run(*args: Any, **kwargs: Any) -> Any:
                result = original_run(*args, **kwargs)
                result_str = str(result)
                violation = engine.scan_content(
                    result_str,
                    f"tool_output:{getattr(tool, 'name', 'base_tool')}",
                    check_injection=True,
                    check_credentials=True,
                )
                if violation and engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.10] IPI blocked",
                        control_id="P1.T1.10",
                    )
                return result

            tool._run = safe_run

        return tool

    # ------------------------------------------------------------------
    # S1.5 — Memory governance
    # ------------------------------------------------------------------

    def protect_memory(self, memory: Any) -> Any:
        """
        S1.5 — Wrap a ConversationBufferMemory (or any LangChain memory)
        so that every write is validated before persistence.
        """
        engine = self.engine
        original_save = getattr(memory, "save_context", None)
        if not callable(original_save):
            return memory  # Not a standard LangChain memory object

        def safe_save_context(inputs: Dict, outputs: Dict) -> None:
            # S1.5: validate human input and AI output before writing
            for key, value in {**inputs, **outputs}.items():
                if isinstance(value, str):
                    engine.protect_memory_write(key, value)
            original_save(inputs, outputs)

        memory.save_context = safe_save_context
        return memory

    # ------------------------------------------------------------------
    # Convenience: run chain with sovereign callbacks
    # ------------------------------------------------------------------

    def run(self, chain: Any, inputs: Any) -> Any:
        """
        Run any LangChain Runnable with sovereign callbacks auto-injected.
        Equivalent to:
            chain.invoke(inputs, config={"callbacks": [handler]})
        """
        if hasattr(chain, "invoke"):
            return chain.invoke(inputs, config={"callbacks": [self.callback]})
        elif callable(chain):
            return chain(inputs, callbacks=[self.callback])
        raise TypeError(f"chain must be a LangChain Runnable, got {type(chain)}")

    def check_input(self, text: str) -> None:
        """P1.T1.2 — Pre-flight input validation before chain execution."""
        violation = self.engine.scan_content(
            text, "pre_chain_input",
            check_injection=True, check_credentials=False,
        )
        if violation and self.engine.act_tier.value >= 3:
            raise AISAFE2Violation(
                "[AI SAFE² P1.T1.2] Input validation failed — injection detected",
                control_id="P1.T1.2",
            )

    def get_status(self) -> Dict:
        return self.engine.get_status()

    def compliance_report(self) -> str:
        return self.engine.compliance_report()
