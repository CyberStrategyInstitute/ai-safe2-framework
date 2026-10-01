import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pr-agent.yml"
CONFIG = ROOT / ".pr_agent.toml"


def _workflow_value(name: str) -> str:
    text = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(rf"^\s{{6}}{re.escape(name)}:\s+(.+)$", text, re.MULTILINE)
    assert match, f"missing {name} from PR-Agent job policy"
    return match.group(1).strip().strip("'")


def test_provider_chain_is_pinned_and_consistent():
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["config"]
    workflow_primary = _workflow_value("PR_AGENT_PRIMARY_MODEL")
    workflow_fallbacks = json.loads(_workflow_value("PR_AGENT_FALLBACK_MODELS"))

    assert workflow_primary == config["model"]
    assert workflow_fallbacks == config["fallback_models"]
    assert "openrouter/free" not in [workflow_primary, *workflow_fallbacks]
    assert all(model != "openrouter/auto" for model in [workflow_primary, *workflow_fallbacks])
    assert workflow_primary == "openrouter/qwen/qwen3.8-27b:free"
    assert workflow_fallbacks == ["gpt-5.6-luna"]


def test_provider_policy_preserves_bounded_attempts_and_evidence():
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["config"]
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert config["num_retries"] == 0
    assert config["retry_same_model_on_timeout"] is False
    assert config["ai_timeout"] == 75
    assert config["max_model_tokens"] == 64000
    assert config["output_run_details"] is True
    assert config["output_run_cost"] is True
    assert "provider_policy:" in workflow
    assert "fallback_models: JSON.parse(process.env.FALLBACK_MODELS)" in workflow
    assert "request_timeout_seconds: Number(process.env.REQUEST_TIMEOUT_SECONDS)" in workflow
    assert "max_model_tokens: Number(process.env.MAX_MODEL_TOKENS)" in workflow
    assert "id: pr-agent-free" in workflow
    assert "id: free-publication" in workflow
    assert "id: pr-agent-openai" in workflow
    assert "timeout-minutes: 3" in workflow
    assert "timeout-minutes: 5" in workflow
    assert "fallback_invoked: fallbackInvoked" in workflow
    assert "active_failure_count: activeFailures.length" in workflow
    assert "provider_execution:" in workflow
    assert "selected_model: modelMatch?.[1] || null" in workflow
    assert "final_model: observedModels.at(-1) || null" in workflow


def test_unrelated_pr_comments_cannot_cancel_an_active_review():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "!startsWith(github.event.comment.body, '/review')" in workflow
    assert "github.run_id || 'review'" in workflow
    assert "cancel-in-progress: true" in workflow
