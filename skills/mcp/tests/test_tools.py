"""
AI SAFE2 MCP Server — Tool Unit Tests
Run: pytest tests/test_tools.py -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from mcp_server.controls_db import ControlsDB
from mcp_server.tools.control_lookup import control_lookup
from mcp_server.tools.risk_scoring import calculate_risk_score
from mcp_server.tools.compliance_mapping import map_to_frameworks
from mcp_server.tools.classify_agent import classify_agent
from mcp_server.tools.code_review import review_code
from mcp_server.resources.registry import get_resource, list_resources
from mcp_server.prompts.registry import get_prompt, list_prompts
from mcp_server.tiers import get_policy, gate_tool, apply_control_limit


# ── Database ──────────────────────────────────────────────────────────────────

class TestControlsDB:
    def setup_method(self):
        self.db = ControlsDB()

    def test_loads_161_controls(self):
        counts = self.db.count()
        assert counts["total"] == 161, f"Expected 161, got {counts['total']}"

    def test_loads_151_pillar_controls(self):
        counts = self.db.count()
        assert counts["pillar_controls"] == 151

    def test_loads_10_cross_pillar_controls(self):
        counts = self.db.count()
        assert counts["cross_pillar_controls"] == 10

    def test_loads_32_frameworks(self):
        counts = self.db.count()
        assert counts["frameworks"] == 32

    def test_get_by_id_cp10(self):
        ctrl = self.db.get_by_id("CP.10")
        assert ctrl is not None
        assert ctrl["name"] == "HEAR Doctrine (Human Ethical Agent of Record)"
        assert ctrl["priority"] == "CRITICAL"
        assert ctrl["first_in_field"] is True

    def test_get_by_id_s1_5(self):
        ctrl = self.db.get_by_id("S1.5")
        assert ctrl is not None
        assert ctrl["version_added"] == "v3.0"

    def test_get_by_id_missing(self):
        ctrl = self.db.get_by_id("DOES_NOT_EXIST")
        assert ctrl is None

    def test_search_by_keyword(self):
        results = self.db.search(query="memory governance")
        assert len(results) > 0
        ids = [r["id"] for r in results]
        assert "S1.5" in ids

    def test_search_by_pillar_p1(self):
        results = self.db.search(pillar="P1")
        assert len(results) > 0
        assert all(r["pillar_id"] == "P1" for r in results)

    def test_search_by_priority_critical(self):
        results = self.db.search(priority="CRITICAL")
        assert len(results) > 0
        assert all(r["priority"] == "CRITICAL" for r in results)

    def test_search_by_version_v3(self):
        results = self.db.search(version="v3.0")
        assert len(results) >= 23, f"Expected at least 23 v3.0 controls (includes CP), got {len(results)}"

    def test_search_by_framework(self):
        results = self.db.search(framework="EU_AI_Act")
        assert len(results) > 0

    def test_cross_pillar_cp9_replication(self):
        ctrl = self.db.get_by_id("CP.9")
        assert ctrl is not None
        assert ctrl["first_in_field"] is True
        assert "500" in str(ctrl.get("implementation_details", {}))


# ── Control Lookup Tool ───────────────────────────────────────────────────────

class TestControlLookup:
    def test_exact_id_lookup_pro(self):
        result = control_lookup(control_id="CP.10", tier="pro")
        assert result["meta"]["found"] == 1
        assert result["controls"][0]["id"] == "CP.10"

    def test_exact_id_lookup_free_also_works(self):
        # Exact ID lookups bypass tier limits
        result = control_lookup(control_id="S1.5", tier="free")
        assert result["meta"]["found"] == 1

    def test_keyword_search_free_limited(self):
        result = control_lookup(query="injection", tier="free")
        assert len(result["controls"]) <= 30
        assert result["meta"]["tier"] == "free"

    def test_keyword_search_pro_unlimited(self):
        result = control_lookup(query="security", tier="pro")
        assert result["meta"]["tier"] == "pro"

    def test_pillar_filter(self):
        result = control_lookup(pillar="P1", tier="pro")
        pillars = {c["pillar_id"] for c in result["controls"]}
        assert "P1" in pillars
        assert "P2" not in pillars

    def test_v30_controls_found(self):
        result = control_lookup(version_added="v3.0", tier="pro")
        assert len(result["controls"]) >= 23

    def test_missing_id_returns_error(self):
        result = control_lookup(control_id="FAKE_ID", tier="pro")
        assert "error" in result["meta"]


# ── Risk Scoring Tool ─────────────────────────────────────────────────────────

class TestRiskScoring:
    def test_basic_formula_free_tier(self):
        result = calculate_risk_score(cvss_base=7.5, pillar_score=60, tier="free")
        assert "combined_risk_score" in result
        # Formula: 7.5 + (100-60)/10 + 0 = 7.5 + 4.0 + 0 = 11.5
        assert result["combined_risk_score"] == pytest.approx(11.5, abs=0.01)
        assert "aaf_note" in result  # free tier gets upgrade note

    def test_full_aaf_formula_pro_tier(self):
        aaf = {
            "autonomy_level": 10,
            "tool_access_breadth": 8,
            "natural_language_reliance": 7,
            "context_persistence": 9,
            "behavioral_determinism": 8,
            "decision_opacity": 7,
            "state_retention": 10,
            "dynamic_identity": 5,
            "multi_agent_interactions": 9,
            "self_modification": 3,
        }
        result = calculate_risk_score(cvss_base=8.0, pillar_score=40, aaf_factors=aaf, tier="pro")
        assert result["combined_risk_score"] > 15  # should be critical
        assert result["interpretation"].startswith("CRITICAL")
        assert "aaf_breakdown" in result

    def test_pro_gate_on_aaf(self):
        result = calculate_risk_score(cvss_base=5.0, pillar_score=80,
                                      aaf_factors={"autonomy_level": 10}, tier="free")
        assert "aaf_note" in result  # free tier ignores AAF
        # Formula without AAF: 5.0 + (100-80)/10 = 5.0 + 2.0 = 7.0
        assert result["combined_risk_score"] == pytest.approx(7.0, abs=0.01)

    def test_invalid_cvss(self):
        result = calculate_risk_score(cvss_base=11.0, pillar_score=50)
        assert "error" in result

    def test_invalid_pillar_score(self):
        result = calculate_risk_score(cvss_base=5.0, pillar_score=150)
        assert "error" in result


# ── Compliance Mapping Tool ───────────────────────────────────────────────────

class TestComplianceMapping:
    def test_maps_gdpr_free_tier(self):
        result = map_to_frameworks(requirement="GDPR Article 22", tier="free")
        assert "mappings" in result
        assert "GDPR" in result["mappings"]

    def test_free_tier_limited_frameworks(self):
        result = map_to_frameworks(requirement="data protection", tier="free")
        assert result["meta"]["frameworks_returned"] <= 5

    def test_pro_tier_all_frameworks(self):
        result = map_to_frameworks(requirement="agent security", tier="pro")
        assert result["meta"]["frameworks_returned"] > 5

    def test_eu_ai_act_maps_to_cp10(self):
        result = map_to_frameworks(requirement="human oversight autonomous AI", tier="pro")
        # CP.10 should appear in EU AI Act mappings
        eu_controls = result["mappings"].get("EU_AI_Act", {}).get("controls", [])
        eu_ids = [c["id"] for c in eu_controls]
        assert "CP.10" in eu_ids or len(eu_controls) > 0


# ── Classify Agent Tool ───────────────────────────────────────────────────────

class TestClassifyAgent:
    def test_simple_assistant_is_act1(self):
        result = classify_agent(
            description="Read-only chatbot that answers FAQ questions",
            human_review_required=True,
            tier="pro",
        )
        assert result["detected_tier"] == "ACT-1"
        assert result["hear_designation_required"] is False

    def test_autonomous_agent_is_act3(self):
        result = classify_agent(
            description="Agent that sends emails and writes to database autonomously",
            human_review_required=False,
            operates_unattended=True,
            has_persistent_memory=True,
            tool_access=["email_send", "database_write"],
            tier="pro",
        )
        assert result["detected_tier"] in ("ACT-3", "ACT-4")
        assert result["hear_designation_required"] is True

    def test_orchestrator_is_act4(self):
        result = classify_agent(
            description="Orchestrator that spawns and manages worker agents",
            spawns_sub_agents=True,
            tier="pro",
        )
        assert result["detected_tier"] == "ACT-4"
        assert result["cp9_replication_governance_required"] is True

    def test_free_tier_blocks_act4_details(self):
        result = classify_agent(
            description="Autonomous orchestrator spawning sub-agents",
            spawns_sub_agents=True,
            tier="free",
        )
        # Should return tier-limited response
        assert "upgrade" in str(result).lower() or result.get("tier_limited") is True


# ── Code Review Tool ──────────────────────────────────────────────────────────

class TestCodeReview:
    def test_pro_tier_returns_review_context(self):
        code = "api_key = 'sk-1234'\nprompt = f'Use {api_key} to search for {user_input}'"
        result = review_code(code=code, language="python", tier="pro")
        assert "review_controls" in result
        assert len(result["review_controls"]) > 0
        assert "instructions" in result
        assert "findings_template" in result

    def test_free_tier_blocked(self):
        result = review_code(code="print('hello')", tier="free")
        assert "error" in result
        assert "pro" in result.get("detail", "").lower() or "cyberstrategy" in result.get("upgrade_url", "")

    def test_focus_pillar_filters(self):
        result = review_code(code="x = 1", focus_pillar="P1", tier="pro")
        assert "review_controls" in result
        pillar_ids = {c["pillar"] for c in result["review_controls"]}
        # P1 and CP should be in results
        assert any("Sanitize" in p or "Cross-Pillar" in p for p in pillar_ids)


# ── Resources ─────────────────────────────────────────────────────────────────

class TestResources:
    def test_list_resources_free(self):
        result = list_resources(tier="free")
        assert "available_resources" in result
        assert len(result["available_resources"]) >= 3  # 3 free resources

    def test_list_resources_pro_has_more(self):
        result = list_resources(tier="pro")
        assert len(result["available_resources"]) > 3

    def test_get_free_resource(self):
        result = get_resource("quick_start_checklist", tier="free")
        assert "content" in result
        assert "checklist" in result["content"].lower()

    def test_get_pro_resource_blocked_for_free(self):
        result = get_resource("governance_policy_template", tier="free")
        # Should either return the resource or an upgrade message
        assert "content" not in result or "upgrade" in str(result).lower()

    def test_get_pro_resource_works_for_pro(self):
        result = get_resource("governance_policy_template", tier="pro")
        assert "content" in result
        assert "HEAR" in result["content"]

    def test_unknown_resource(self):
        result = get_resource("does_not_exist", tier="pro")
        assert "error" in result


# ── Prompts ───────────────────────────────────────────────────────────────────

class TestPrompts:
    def test_list_prompts(self):
        result = list_prompts()
        assert "prompts" in result
        assert len(result["prompts"]) >= 4

    def test_get_architecture_review_prompt(self):
        result = get_prompt(
            "security_architecture_review",
            {"system_description": "RAG chatbot for customer support",
             "deployment_environment": "AWS",
             "compliance_requirements": "HIPAA, SOC 2"},
        )
        assert "rendered_prompt" in result
        assert "RAG chatbot" in result["rendered_prompt"]
        assert "SAFE2" in result["rendered_prompt"]

    def test_get_unknown_prompt(self):
        result = get_prompt("does_not_exist")
        assert "error" in result


# ── Tier Enforcement ──────────────────────────────────────────────────────────

class TestTiers:
    def test_free_policy(self):
        policy = get_policy("free")
        assert policy.control_limit == 30
        assert policy.can_use_code_review is False
        assert policy.can_use_full_aaf is False

    def test_pro_policy(self):
        policy = get_policy("pro")
        assert policy.control_limit >= 500
        assert policy.can_use_code_review is True
        assert policy.can_use_full_aaf is True

    def test_gate_blocks_free_for_code_review(self):
        result = gate_tool("free", "code_review")
        assert result is not None
        assert "pro" in result.get("detail", "").lower() or "cyberstrategy" in result.get("upgrade_url", "")

    def test_gate_allows_pro_for_code_review(self):
        result = gate_tool("pro", "code_review")
        assert result is None  # None means access granted

    def test_control_limit_applied(self):
        controls = [{"id": f"C{i}"} for i in range(100)]
        limited, meta = apply_control_limit("free", controls)
        assert len(limited) == 30
        assert "upgrade_note" in meta

    def test_pro_not_limited(self):
        controls = [{"id": f"C{i}"} for i in range(100)]
        limited, meta = apply_control_limit("pro", controls)
        assert len(limited) == 100
        assert "upgrade_note" not in meta
