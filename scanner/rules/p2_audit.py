"""
AI SAFE2 v3.0 Scanner — Pillar 2: Audit & Inventory Rules
Covers: P2.T3.x (Audit), P2.T4.x (Inventory), A2.3-A2.6 (v3.0 new controls)
"""
from __future__ import annotations

import re
from .base import Rule


def _check_llm_call_without_logging(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    P2.T3.1 + A2.5 — Real-Time Activity Logging / Semantic Execution Trace Logging
    Detect LLM API calls that are not wrapped in any logging context.
    """
    findings = []
    # Patterns that indicate an LLM API call
    llm_call_patterns = [
        r"\.chat\.completions\.create\(", r"client\.messages\.create\(",
        r"openai\.ChatCompletion", r"anthropic\.messages",
        r"\.invoke\(", r"\.run\(", r"\.generate\(", r"\.predict\(",
        r"chain\.invoke", r"llm\.invoke", r"agent\.run",
        r"llm\(", r"model\(",
    ]
    # Logging indicators
    log_indicators = {
        "log", "logger", "logging", "audit", "trace", "span", "record",
        "langsmith", "tracing", "langfuse", "phoenix", "opentelemetry",
        "structlog", "log_llm", "audit_log", "a2_5", "execution_trace",
    }

    for i, line in enumerate(lines):
        for pat in llm_call_patterns:
            if re.search(pat, line, re.IGNORECASE):
                # Check ±5 lines for logging context
                start = max(0, i - 5)
                end = min(len(lines), i + 5)
                context = " ".join(lines[start:end]).lower()
                if not any(w in context for w in log_indicators):
                    findings.append((
                        i + 1,
                        f"LLM API call without logging context: {line.strip()[:60]}"
                    ))
                break
    return findings


def _check_missing_owner_of_record(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    A2.4 — Dynamic Agent State Inventory
    Detect agent definitions in config files missing owner_of_record field.
    """
    findings = []
    if not any(filepath.endswith(ext) for ext in (".json", ".yaml", ".yml", ".toml")):
        return []

    # Agent definition indicators in config
    agent_markers = [
        r'"agent"', r'"agents"', r'"agent_config"', r'"agent_definition"',
        r'agent:', r'agents:', r'agent_config:', r'"type".*agent',
        r'"act_tier"', r'"acl_tier"',
    ]
    has_agent = any(re.search(m, content, re.IGNORECASE) for m in agent_markers)
    if not has_agent:
        return []

    # Check for owner fields
    ownership_fields = {
        "owner_of_record", "owner", "hear_agent_of_record",
        "control_plane_id", "agent_owner", "responsible_party"
    }
    has_owner = any(f in content.lower() for f in ownership_fields)

    if not has_owner:
        findings.append((
            1,
            "Agent config missing owner_of_record field — required by A2.4 for all deployed agents"
        ))
    return findings


def _check_rag_corpus_without_tracking(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    A2.6 — RAG Corpus Diff Tracking
    Detect vector store updates without hash/version tracking.
    """
    findings = []
    update_patterns = [
        r"\.update\s*\(", r"\.upsert\s*\(", r"\.add_documents\s*\(",
        r"\.add_texts\s*\(", r"vectorstore\.add", r"collection\.update",
        r"index\.upsert",
    ]
    tracking_words = {
        "hash", "sha256", "checksum", "version", "revision", "diff",
        "corpus_version", "a2_6", "track", "changelog", "audit"
    }

    for i, line in enumerate(lines):
        for pat in update_patterns:
            if re.search(pat, line, re.IGNORECASE):
                context = " ".join(lines[max(0, i - 3):i + 3]).lower()
                if not any(w in context for w in tracking_words):
                    findings.append((
                        i + 1,
                        f"RAG corpus update without hash/version tracking: {line.strip()[:60]}"
                    ))
    return findings


P2_RULES: list[Rule] = [

    # ── P2.T3.x Audit ─────────────────────────────────────────────────────────

    # P2.T3.1 + A2.5 — LLM calls without logging
    Rule(
        control_id="A2.5",
        severity="HIGH",
        description="LLM API call without logging or tracing context — "
                    "no semantic execution trace present.",
        remediation="Apply A2.5: wrap every LLM call in a logging context that captures "
                    "the full reasoning chain, tool calls, and memory operations to an "
                    "append-only audit store. Use LangSmith, Langfuse, or OpenTelemetry.",
        check_fn=_check_llm_call_without_logging,
        file_exts=(".py", ".js", ".ts"),
    ),

    # Vulnerability scanning references (P2.T3.10)
    Rule(
        control_id="P2.T3.10",
        severity="MEDIUM",
        description="requirements.txt or pyproject.toml detected — "
                    "verify all AI framework dependencies are scanned against CVE database.",
        remediation="Apply P2.T3.10: integrate pip-audit or safety into CI/CD. "
                    "Pin exact versions and update on CVE notification. "
                    "Run: pip-audit -r requirements.txt",
        pattern=r"(langchain|openai|anthropic|transformers|torch|tensorflow|chromadb|pinecone)",
        file_exts=("requirements.txt", "pyproject.toml", "package.json"),
    ),

    # ── P2.T4.x Inventory ─────────────────────────────────────────────────────

    # Missing agent registry / owner (A2.4)
    Rule(
        control_id="A2.4",
        severity="HIGH",
        description="Agent configuration file detected without owner_of_record field — "
                    "violates A2.4 Dynamic Agent State Inventory requirement.",
        remediation="Add owner_of_record, hear_agent_of_record (if ACT-3/4), and "
                    "control_plane_id to every agent deployment configuration.",
        check_fn=_check_missing_owner_of_record,
        file_exts=(".json", ".yaml", ".yml", ".toml"),
    ),

    # Missing model catalog (P2.T4.2)
    Rule(
        control_id="P2.T4.2",
        severity="MEDIUM",
        description="Model loaded by name/path without version pinning or provenance tracking.",
        remediation="Apply P2.T4.2: pin exact model version strings. "
                    "Maintain a model catalog with version, training data reference, and SHA-256 hash.",
        pattern=r'from_pretrained\s*\(\s*["\'](?!.*["\s]revision)',
        file_exts=(".py",),
    ),

    # ── A2.3-A2.6 New v3.0 Controls ──────────────────────────────────────────

    # A2.3 — Model Lineage Provenance
    Rule(
        control_id="A2.3",
        severity="HIGH",
        description="Model file loaded without SHA-256 integrity verification — "
                    "no lineage provenance check present.",
        remediation="Apply A2.3: verify SHA-256 hash against a signed manifest before loading. "
                    "Use OpenSSF Model Signing (Sigstore/Cosign) for model provenance chain.",
        pattern=r"(torch\.load|joblib\.load|pickle\.load|load_model|from_pretrained)",
        file_exts=(".py",),
    ),

    # A2.6 — RAG Corpus Diff Tracking
    Rule(
        control_id="A2.6",
        severity="HIGH",
        description="Vector store or RAG corpus updated without hash-verified diff tracking — "
                    "behavioral changes cannot be correlated to corpus changes.",
        remediation="Apply A2.6: create a hash-verified change log for every retrieval layer update. "
                    "Log document hash, timestamp, and operation type to an auditable store.",
        check_fn=_check_rag_corpus_without_tracking,
        file_exts=(".py", ".js", ".ts"),
    ),
]
