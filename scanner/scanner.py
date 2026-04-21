"""
AI SAFE² v3.0 Static Analysis Engine
Copyright (c) 2026 Cyber Strategy Institute

Upgraded from v2.1 (7 patterns, 4 controls) to v3.0:
  - 40+ detection rules across all 5 pillars + CP.1-CP.10
  - Python AST structural analysis for agent topology detection
  - Config file inspection (n8n JSON, YAML agent definitions)
  - ACT tier estimation from code signals
  - CP.9/CP.10/CP.8 governance presence checks
  - v3.0 Combined Risk Score formula (CVSS + Pillar + AAF estimate)
  - 32-framework compliance mapping via ai-safe2-controls-v3.0.json
"""
from __future__ import annotations

import ast
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Try to load rules; fall back to empty if import fails
try:
    from .rules import ALL_RULES
    from .rules.cross_pillar import ACTEstimate, estimate_act_tier, CP_RULES
    from .rules.base import Finding, Rule, is_comment_line, is_test_file
except ImportError:
    from rules import ALL_RULES
    from rules.cross_pillar import ACTEstimate, estimate_act_tier, CP_RULES
    from rules.base import Finding, Rule, is_comment_line, is_test_file


# ── Pydantic models (kept for backward compatibility with v2.1 report.py) ──────

class Violation(BaseModel):
    """v2.1 compatible model — wraps Finding."""
    control_id: str
    severity: str
    file_path: str
    line_number: int
    evidence: str
    remediation: str
    # v3.0 extensions
    control_name: str = ""
    pillar: str = ""
    compliance_frameworks: list = []
    description: str = ""


class ScanResult(BaseModel):
    score: float
    verdict: str
    violations: list[Violation]
    controls_failed: list[str]
    meta: dict[str, Any]
    # v3.0 extensions
    act_estimate: dict = {}
    risk_formula_components: dict = {}
    governance_gaps: list[str] = []


# ── Controls DB (lightweight, standalone) ─────────────────────────────────────

class ControlsLoader:
    """
    Loads ai-safe2-controls-v3.0.json to enrich findings with control metadata.
    Works standalone — scanner functions without the JSON, just with less detail.
    """

    def __init__(self, json_path: Path | None = None):
        self._index: dict[str, dict] = {}
        self._risk_formula: dict = {}
        self._loaded = False

        if json_path is None:
            # Try common paths relative to this file
            candidates = [
                Path(__file__).parent.parent / "skills" / "mcp" / "data" / "ai-safe2-controls-v3.0.json",
                Path(__file__).parent.parent / "skills_output" / "mcp" / "data" / "ai-safe2-controls-v3.0.json",
                Path(__file__).parent / "ai-safe2-controls-v3.0.json",
                Path.cwd() / "ai-safe2-controls-v3.0.json",
            ]
            for candidate in candidates:
                if candidate.exists():
                    json_path = candidate
                    break

        if json_path and Path(json_path).exists():
            try:
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)
                for ctrl in data.get("pillar_controls", []):
                    self._index[ctrl["id"]] = ctrl
                for ctrl in data.get("cross_pillar_controls", []):
                    self._index[ctrl["id"]] = ctrl
                self._risk_formula = data.get("risk_formula", {})
                self._loaded = True
            except Exception:
                pass  # Degrade gracefully

    def get(self, control_id: str) -> dict:
        return self._index.get(control_id, {})

    def enrich_finding(self, finding: Finding) -> Finding:
        ctrl = self.get(finding.control_id)
        if ctrl:
            finding.control_name = ctrl.get("name", finding.control_id)
            finding.pillar = ctrl.get("pillar_name", "")
            finding.compliance_frameworks = ctrl.get("compliance_frameworks", [])
            finding.act_minimum = ctrl.get("act_minimum", [])
            finding.builder_problem = ctrl.get("builder_problem", "")
        return finding

    @property
    def loaded(self) -> bool:
        return self._loaded


# ── Entropy Detection ─────────────────────────────────────────────────────────

def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    entropy = 0.0
    for x in range(256):
        p_x = float(text.count(chr(x))) / len(text)
        if p_x > 0:
            entropy -= p_x * math.log2(p_x)
    return entropy


# Strings that produce high entropy but are not secrets
_ENTROPY_FALSE_POSITIVE_PATTERNS = re.compile(
    r"(https?://|base64|data:image|sha256:[a-f0-9]+|[a-f0-9]{64}|"
    r"-----BEGIN|-----END|import\s+|from\s+\w|version\s*=|"
    r"\.(png|jpg|svg|ico|woff|ttf)|<!DOCTYPE|<html|xmlns)"
)


def _check_entropy(word: str, line: str) -> bool:
    """Return True if word is likely a secret based on entropy."""
    if len(word) < 20:
        return False
    if _ENTROPY_FALSE_POSITIVE_PATTERNS.search(word):
        return False
    if "/" in word or "." in word or "\\" in word:
        return False
    # Skip pure hex strings (hashes are not secrets)
    if re.fullmatch(r"[a-fA-F0-9]+", word):
        return False
    # Skip common programming tokens
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{19,}", word):
        return len(set(word)) > 10  # require character diversity
    return _shannon_entropy(word) > 4.5


# ── AST Structural Analysis ───────────────────────────────────────────────────

class AgentStructureVisitor(ast.NodeVisitor):
    """
    Python AST visitor that extracts structural signals about agent architecture.
    Used for ACT tier estimation enrichment and structural findings.
    """

    def __init__(self):
        self.tool_definitions: list[str] = []
        self.spawn_calls: list[tuple[int, str]] = []
        self.llm_calls: list[tuple[int, str]] = []
        self.memory_writes: list[tuple[int, str]] = []
        self.has_rate_limit: bool = False
        self.has_error_handling: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Detect tool definitions via decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "tool":
                self.tool_definitions.append(node.name)
            elif isinstance(decorator, ast.Attribute) and decorator.attr == "tool":
                self.tool_definitions.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        call_str = ast.unparse(node) if hasattr(ast, "unparse") else ""
        lineno = node.lineno

        # Spawning signals
        spawn_patterns = ("spawn_agent", "create_agent", "invoke_agent",
                          "Process(", "Thread(", "create_task")
        if any(p in call_str for p in spawn_patterns):
            self.spawn_calls.append((lineno, call_str[:60]))

        # LLM calls
        llm_patterns = ("completions.create", "messages.create", "llm.invoke",
                        "agent.run", "chain.invoke", "generate(")
        if any(p in call_str for p in llm_patterns):
            self.llm_calls.append((lineno, call_str[:60]))

        # Memory writes
        write_patterns = ("upsert(", "add_documents(", "add_texts(", "save_context(")
        if any(p in call_str for p in write_patterns):
            self.memory_writes.append((lineno, call_str[:60]))

        # Rate limiting
        rate_patterns = ("rate_limit", "throttle", "sleep(", "RateLimiter")
        if any(p in call_str for p in rate_patterns):
            self.has_rate_limit = True

        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.has_error_handling = True
        self.generic_visit(node)


def _run_ast_analysis(content: str, filepath: str) -> list[Finding]:
    """Run AST structural analysis on Python files."""
    findings = []
    if not filepath.endswith(".py"):
        return []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    visitor = AgentStructureVisitor()
    visitor.visit(tree)

    # Flag spawn calls noted but without lineage in file
    if visitor.spawn_calls:
        lineage_words = {"lineage", "parent_did", "delegation_depth", "cp9", "chain_id"}
        if not any(w in content.lower() for w in lineage_words):
            for lineno, call in visitor.spawn_calls[:3]:  # max 3 per file
                findings.append(Finding(
                    control_id="CP.9",
                    severity="CRITICAL",
                    file_path=filepath,
                    line_number=lineno,
                    evidence=call,
                    description="Agent spawning without CP.9 lineage governance (AST detected).",
                    remediation="Add lineage_token with parent_did, chain_id, delegation_depth, TTL. "
                                "Enforce max delegation hops at gateway layer.",
                ))

    # Flag LLM calls without error handling
    if visitor.llm_calls and not visitor.has_error_handling:
        lineno, call = visitor.llm_calls[0]
        findings.append(Finding(
            control_id="P3.T5.4",
            severity="HIGH",
            file_path=filepath,
            line_number=lineno,
            evidence=call,
            description="LLM API calls found with no exception handling in this file (AST detected).",
            remediation="Wrap LLM API calls in try/except. Define fallback behavior and timeout.",
        ))

    # Flag tool definitions without monitoring
    if visitor.tool_definitions:
        monitoring_words = {"monitor", "baseline", "track", "audit", "m4_5"}
        if not any(w in content.lower() for w in monitoring_words):
            findings.append(Finding(
                control_id="M4.5",
                severity="HIGH",
                file_path=filepath,
                line_number=1,
                evidence=f"Tools: {', '.join(visitor.tool_definitions[:5])}",
                description=f"{len(visitor.tool_definitions)} tool definition(s) without invocation monitoring (AST detected).",
                remediation="Establish tool invocation baselines. Monitor for unexpected tools, "
                            "anomalous parameters, and frequency spikes.",
            ))

    return findings


# ── Main Scanner ──────────────────────────────────────────────────────────────

# File extensions the scanner processes
SUPPORTED_EXTENSIONS = (
    ".py", ".js", ".ts", ".env", ".json", ".yaml", ".yml", ".toml",
    ".md", "requirements.txt", "requirements-dev.txt", "pyproject.toml",
    "package.json", "setup.cfg",
)

# Directories to always skip
SKIP_DIRS = {"node_modules", ".git", "venv", ".venv", "__pycache__",
             ".pytest_cache", "dist", "build", ".tox", ".eggs"}


class StaticScanner:

    def __init__(self, config_path: str | None = None, controls_json: str | None = None):
        self.config_path = config_path
        self.controls = ControlsLoader(Path(controls_json) if controls_json else None)
        self.rules: list[Rule] = ALL_RULES

    def scan_project(self, root_path: str) -> ScanResult:
        findings: list[Finding] = []
        act_estimates: list[tuple[str, ACTEstimate]] = []  # (filepath, estimate)

        for root, dirs, files in os.walk(root_path):
            # Prune skip dirs in-place so os.walk doesn't descend
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                full_path = Path(root) / filename
                filepath_str = str(full_path)

                # Check if extension is supported
                if not any(
                    filepath_str.endswith(ext) or filename == ext
                    for ext in SUPPORTED_EXTENSIONS
                ):
                    continue

                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.split("\n")
                except Exception:
                    continue

                is_test = is_test_file(filepath_str)

                # ── Line-by-line regex scan ────────────────────────────────
                for i, line in enumerate(lines):
                    # Skip comment lines for most rules
                    if is_comment_line(line, filepath_str):
                        continue

                    # Entropy scan (secrets that bypass regex)
                    if not is_test:
                        for word in line.split():
                            if _check_entropy(word, line):
                                findings.append(Finding(
                                    control_id="P1.T1.4_ADV",
                                    severity="HIGH",
                                    file_path=filepath_str,
                                    line_number=i + 1,
                                    evidence=f"High-entropy token: {word[:12]}... (entropy > 4.5)",
                                    description="High-entropy string detected — may be an embedded secret or token.",
                                    remediation="Verify this is not a credential. Move secrets to "
                                                "environment variables or a secrets manager.",
                                ))

                    # Regex rule scan
                    for rule in self.rules:
                        if rule.pattern is None:
                            continue  # structural rules handled below
                        if rule.file_exts and not any(filepath_str.endswith(e) for e in rule.file_exts):
                            continue
                        if rule.skip_comments and is_comment_line(line, filepath_str):
                            continue
                        if len(line.strip()) < rule.min_length:
                            continue
                        if re.search(rule.pattern, line, re.IGNORECASE):
                            # Reduce noise from test files for non-critical findings
                            if is_test and rule.severity not in ("CRITICAL",):
                                continue
                            findings.append(Finding(
                                control_id=rule.control_id,
                                severity=rule.severity,
                                file_path=filepath_str,
                                line_number=i + 1,
                                evidence=line.strip()[:80],
                                description=rule.description,
                                remediation=rule.remediation,
                            ))

                # ── Structural / check_fn scan ─────────────────────────────
                for rule in self.rules:
                    if rule.check_fn is None:
                        continue
                    if rule.file_exts and not any(filepath_str.endswith(e) for e in rule.file_exts):
                        continue
                    try:
                        hits = rule.check_fn(content, lines, filepath_str)
                        for line_number, evidence in hits:
                            if is_test and rule.severity not in ("CRITICAL",):
                                continue
                            findings.append(Finding(
                                control_id=rule.control_id,
                                severity=rule.severity,
                                file_path=filepath_str,
                                line_number=line_number,
                                evidence=evidence[:80],
                                description=rule.description,
                                remediation=rule.remediation,
                            ))
                    except Exception:
                        pass  # Never let a rule failure abort the scan

                # ── AST structural analysis (Python only) ─────────────────
                if filepath_str.endswith(".py"):
                    ast_findings = _run_ast_analysis(content, filepath_str)
                    findings.extend(ast_findings)

                    # ACT tier estimation for agent files
                    if any(re.search(p, content, re.IGNORECASE) for p in [
                        r"openai\.", r"anthropic\.", r"\.invoke\(", r"agent\.run", r"llm\.predict"
                    ]):
                        estimate = estimate_act_tier(content)
                        if estimate.tier != "N/A":
                            act_estimates.append((filepath_str, estimate))

        # ── Enrich findings with controls JSON metadata ────────────────────
        for f in findings:
            self.controls.enrich_finding(f)

        # ── Deduplicate findings ───────────────────────────────────────────
        seen: set[tuple] = set()
        unique_findings: list[Finding] = []
        for f in findings:
            key = (f.control_id, f.file_path, f.line_number)
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)
        findings = unique_findings

        # ── Score calculation ──────────────────────────────────────────────
        penalty = sum(
            {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1, "INFO": 0}.get(f.severity, 0)
            for f in findings
        )
        raw_score = max(0.0, 100.0 - penalty)

        # Pillar sub-scores
        pillar_scores: dict[str, float] = {}
        for pid in ("P1", "P2", "P3", "P4", "P5", "CP"):
            pillar_findings = [f for f in findings if f.control_id.startswith(pid)]
            p_penalty = sum(
                {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}.get(f.severity, 0)
                for f in pillar_findings
            )
            pillar_scores[pid] = max(0.0, 100.0 - p_penalty * 2)  # harsher per-pillar

        overall_pillar_score = sum(pillar_scores.values()) / max(len(pillar_scores), 1)

        # AAF estimation from code signals (partial — static analysis only)
        aaf_signals = {
            "autonomy_level": 0.0,
            "tool_access_breadth": 0.0,
            "context_persistence": 0.0,
            "multi_agent_interactions": 0.0,
        }
        if act_estimates:
            # Pick the highest-tier estimate
            tier_order = {"ACT-4": 4, "ACT-3": 3, "ACT-2": 2, "ACT-1": 1, "N/A": 0}
            top = max(act_estimates, key=lambda x: tier_order.get(x[1].tier, 0))
            _, est = top
            aaf_signals["autonomy_level"] = {"ACT-4": 10, "ACT-3": 8, "ACT-2": 5, "ACT-1": 2}.get(est.tier, 0)
            if est.cp9_required:
                aaf_signals["multi_agent_interactions"] = 9.0
            if est.hear_required:
                aaf_signals["context_persistence"] = 7.0

        aaf_partial = sum(aaf_signals.values())
        # Use worst CVSS as proxy from severity distribution
        if any(f.severity == "CRITICAL" for f in findings):
            cvss_proxy = 9.0
        elif any(f.severity == "HIGH" for f in findings):
            cvss_proxy = 7.5
        elif any(f.severity == "MEDIUM" for f in findings):
            cvss_proxy = 5.0
        else:
            cvss_proxy = 2.0

        combined_risk = round(
            cvss_proxy + (100 - overall_pillar_score) / 10 + (aaf_partial / 10), 2
        )

        # Verdict
        if raw_score >= 90:
            verdict = "PASS"
        elif raw_score >= 70:
            verdict = "AT RISK"
        elif raw_score >= 50:
            verdict = "FAIL"
        else:
            verdict = "CRITICAL FAIL"

        # Collect governance gaps from ACT estimates
        all_gaps: list[str] = []
        for _, est in act_estimates:
            all_gaps.extend(est.governance_gaps)
        # Deduplicate gaps
        seen_gaps: set[str] = set()
        unique_gaps = []
        for g in all_gaps:
            if g[:50] not in seen_gaps:
                seen_gaps.add(g[:50])
                unique_gaps.append(g)

        # Convert to Violation objects for backward compat
        violations = [
            Violation(
                control_id=f.control_id,
                severity=f.severity,
                file_path=f.file_path,
                line_number=f.line_number,
                evidence=f.evidence,
                remediation=f.remediation,
                control_name=f.control_name,
                pillar=f.pillar,
                compliance_frameworks=f.compliance_frameworks,
                description=f.description,
            )
            for f in findings
        ]

        controls_failed = sorted(set(f.control_id for f in findings))

        # Best ACT estimate summary for meta
        act_summary = {}
        if act_estimates:
            tier_order = {"ACT-4": 4, "ACT-3": 3, "ACT-2": 2, "ACT-1": 1}
            top_file, top_est = max(act_estimates, key=lambda x: tier_order.get(x[1].tier, 0))
            act_summary = {
                "estimated_tier": top_est.tier,
                "confidence": top_est.confidence,
                "signals": top_est.signals[:3],
                "hear_required": top_est.hear_required,
                "cp9_required": top_est.cp9_required,
                "mandatory_controls": top_est.mandatory_controls,
                "source_file": top_file,
            }

        return ScanResult(
            score=round(raw_score, 1),
            verdict=verdict,
            violations=violations,
            controls_failed=controls_failed,
            meta={
                "scanned_path": root_path,
                "framework": "v3.0",
                "framework_url": "https://github.com/CyberStrategyInstitute/ai-safe2-framework",
                "total_files_scanned": len(seen),
                "controls_json_loaded": self.controls.loaded,
                "pillar_scores": {k: round(v, 1) for k, v in pillar_scores.items()},
            },
            act_estimate=act_summary,
            risk_formula_components={
                "formula": "CVSS + ((100 - Pillar_Score) / 10) + (AAF_estimate / 10)",
                "cvss_proxy": cvss_proxy,
                "pillar_score": round(overall_pillar_score, 1),
                "aaf_partial_estimate": round(aaf_partial, 1),
                "combined_risk_score": combined_risk,
                "note": "CVSS and AAF are static-analysis estimates. "
                        "Use the AI SAFE2 MCP risk_score tool for precise calculation.",
            },
            governance_gaps=unique_gaps,
        )
