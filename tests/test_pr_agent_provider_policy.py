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
    assert workflow_fallbacks[-1] == "gpt-5.6-luna"


def test_provider_policy_preserves_bounded_attempts_and_evidence():
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["config"]
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert config["num_retries"] == 0
    assert config["retry_same_model_on_timeout"] is False
    assert config["output_run_details"] is True
    assert config["output_run_cost"] is True
    assert "provider_policy:" in workflow
    assert "fallback_models: JSON.parse(process.env.FALLBACK_MODELS)" in workflow
    assert "provider_execution:" in workflow
    assert "selected_model: modelMatch?.[1] || null" in workflow
    assert "final_model: observedModels.at(-1) || null" in workflow
