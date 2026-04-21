"""
AI SAFE2 v3.0 Scanner — Pillar 5: Evolve & Educate Rules
Covers: P5.T9.x (Evolve), P5.T10.x (Educate), E5.x (v3.0 new controls)
"""
from __future__ import annotations

import re
from .base import Rule


# Known vulnerable version strings for major AI libraries
# Format: (library_name, version_pattern_that_is_vulnerable, description)
VULNERABLE_VERSIONS = [
    # langchain
    ("langchain", r"langchain[=<>!~]+0\.(0|1)\.", "LangChain <0.2 — multiple agent security CVEs"),
    ("langchain-core", r"langchain-core[=<>!~]+0\.(1)\.", "LangChain Core <0.2 — prompt injection exposure"),
    # transformers
    ("transformers", r"transformers[=<>!~]+4\.(2[0-9]|[0-1][0-9])\.", "Hugging Face Transformers <4.30 — deserialization vulnerability"),
    # openai python client
    ("openai", r"openai[=<>!~]+0\.", "OpenAI Python SDK v0.x — deprecated, security updates stopped"),
    # older torch with known pickle issues
    ("torch", r"torch[=<>!~]+1\.", "PyTorch 1.x — unsafe pickle deserialization in torch.load"),
    # requests
    ("requests", r"requests[=<>!~]+2\.([01][0-9])\.", "requests <2.20 — SSRF and redirect vulnerability"),
    # pydantic v1 with known issues
    ("pydantic", r"pydantic[=<>!~]+1\.(0|1|2|3|4|5|6|7|8)\.", "Pydantic <1.9 — validation bypass vulnerability"),
]

# AI framework import patterns that indicate the library is in use
AI_FRAMEWORK_IMPORTS = [
    r"^import\s+langchain", r"^from\s+langchain",
    r"^import\s+openai", r"^from\s+openai",
    r"^import\s+anthropic", r"^from\s+anthropic",
    r"^import\s+transformers", r"^from\s+transformers",
    r"^import\s+torch", r"^from\s+torch",
    r"^import\s+chromadb", r"^from\s+chromadb",
    r"^import\s+pinecone", r"^from\s+pinecone",
    r"^import\s+weaviate", r"^from\s+weaviate",
    r"^import\s+autogen", r"^from\s+autogen",
    r"^import\s+crewai", r"^from\s+crewai",
]


def _check_vulnerable_dependencies(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    P5.T9.4 — Patch Management
    Detect known-vulnerable AI library version pinnings in requirements files.
    """
    findings = []
    for lib_name, vuln_pattern, description in VULNERABLE_VERSIONS:
        if re.search(vuln_pattern, content, re.IGNORECASE):
            for i, line in enumerate(lines):
                if re.search(vuln_pattern, line, re.IGNORECASE):
                    findings.append((
                        i + 1,
                        f"Vulnerable dependency: {description} — {line.strip()[:60]}"
                    ))
    return findings


def _check_missing_adversarial_eval(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    E5.1 — Continuous Adversarial Evaluation Cadence
    Detect CI/CD configs without adversarial evaluation gates.
    """
    findings = []
    if not any(filepath.endswith(ext) for ext in (".yml", ".yaml")):
        return []

    # CI/CD workflow indicators
    ci_markers = [
        "on: push", "on: pull_request", "stages:", "pipeline:",
        "jobs:", "workflow:", "trigger:", "triggers:"
    ]
    has_ci = any(m.lower() in content.lower() for m in ci_markers)
    if not has_ci:
        return []

    # Adversarial evaluation indicators
    eval_words = {
        "adversarial", "red_team", "security_scan", "ai_safe2", "scanner",
        "prompt_injection", "jailbreak", "pentest", "ai_security",
        "e5_1", "eval_gate", "garak", "pyrit",
    }
    has_eval = any(w in content.lower() for w in eval_words)
    if not has_eval:
        findings.append((
            1,
            "CI/CD pipeline detected without adversarial evaluation gate (E5.1 required)"
        ))
    return findings


P5_RULES: list[Rule] = [

    # ── P5.T9.x Evolve ────────────────────────────────────────────────────────

    # P5.T9.4 — Patch Management
    Rule(
        control_id="P5.T9.4",
        severity="HIGH",
        description="Known-vulnerable AI library version pinned in requirements — "
                    "unpatched security vulnerabilities present.",
        remediation="Apply P5.T9.4: update to the patched version immediately. "
                    "Integrate pip-audit or Dependabot for automated CVE monitoring. "
                    "Subscribe to security advisories for all AI frameworks in use.",
        check_fn=_check_vulnerable_dependencies,
        file_exts=("requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.cfg"),
    ),

    Rule(
        control_id="P5.T9.7",
        severity="MEDIUM",
        description="No threat intelligence integration found — no MITRE ATLAS or CVE feed references.",
        remediation="Apply P5.T9.7: integrate MITRE ATLAS and CVE feeds into your security process. "
                    "Use CP.6 AIID incident feedback loop for quarterly threat model updates.",
        pattern=r"(?i)(mitre|atlas|cve|threat_intel|nvd|osv)",
        file_exts=(".py", ".yaml", ".yml", ".json"),
    ),

    # ── E5.1-E5.4 New v3.0 Controls ──────────────────────────────────────────

    # E5.1 — Continuous Adversarial Evaluation Cadence
    Rule(
        control_id="E5.1",
        severity="HIGH",
        description="CI/CD pipeline detected without adversarial evaluation gate — "
                    "the system being deployed is not the system that was tested.",
        remediation="Apply E5.1: add adversarial evaluation gates triggered by model updates, "
                    "prompt changes, and tool additions. Use the AI SAFE2 scanner in CI/CD. "
                    "See: github.com/CyberStrategyInstitute/ai-safe2-framework INTEGRATIONS.md",
        check_fn=_check_missing_adversarial_eval,
        file_exts=(".yml", ".yaml"),
    ),

    Rule(
        control_id="E5.4",
        severity="MEDIUM",
        description="No red-team artifact repository references found — "
                    "security findings are not being systematically retained.",
        remediation="Apply E5.4: maintain a structured red-team artifact repository. "
                    "Every red-team exercise must produce a documented artifact with "
                    "attack type, affected component, AIVSS score, and remediation control.",
        pattern=r"(?i)(red.?team|pentest|adversarial.?test|security.?test|e5_4|artifact.?repo)",
        file_exts=(".py", ".yaml", ".yml", ".md", ".json"),
    ),
]
