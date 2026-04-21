"""
AI SAFE2 v3.0 Scanner — Pillar 1: Sanitize & Isolate Rules
Covers: P1.T1.x (Sanitize), P1.T2.x (Isolate), S1.3-S1.7 (v3.0 new controls)
"""
from __future__ import annotations

import re
from .base import Rule


def _check_indirect_injection(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    P1.T1.10 — Indirect Injection Surface Coverage
    Detect user/external content flowing into LLM calls or tool invocations
    without intermediate sanitization — the indirect injection attack surface.
    """
    findings = []
    # Patterns that indicate external content reaching an LLM context unguarded
    source_patterns = [
        r"email\.body", r"email_body", r"message\.content", r"retrieved_doc",
        r"search_result", r"web_page", r"rag_result", r"retrieval_result",
        r"tool_output", r"api_response", r"read_text\(", r"requests\.get",
        r"httpx\.get", r"fetch\(", r"\.content\.decode",
    ]
    sink_patterns = [
        r'messages\s*=\s*\[', r'prompt\s*=\s*f["\']', r'system_prompt\s*\+',
        r'\.invoke\(', r'\.run\(', r'chat_completion', r'create\(messages',
        r'tool_call', r'function_call',
    ]
    # Simple heuristic: if a source and a sink appear within 10 lines of each other
    # without a sanitize/clean/validate call in between
    sanitize_words = {"sanitize", "clean", "validate", "strip_html", "filter",
                      "escape", "encode", "guard", "check_injection"}

    for i, line in enumerate(lines):
        for src_pat in source_patterns:
            if re.search(src_pat, line, re.IGNORECASE):
                # Look ahead 10 lines for a sink
                window = lines[i:min(i + 10, len(lines))]
                window_text = " ".join(window).lower()
                has_sanitize = any(w in window_text for w in sanitize_words)
                has_sink = any(re.search(sp, window_text, re.IGNORECASE) for sp in sink_patterns)
                if has_sink and not has_sanitize:
                    findings.append((
                        i + 1,
                        f"External content '{line.strip()[:50]}' may reach LLM without sanitization"
                    ))
                    break  # one finding per source line
    return findings


def _check_memory_write_governance(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    S1.5 — Memory Governance Boundary Controls
    Detect vector DB writes and agent memory operations without governance wrappers.
    """
    findings = []
    write_patterns = [
        r"\.upsert\(", r"\.add_documents\(", r"\.add_texts\(", r"\.insert\(",
        r"\.index\(", r"vectorstore\.add", r"memory\.save", r"\.save_context\(",
        r"vector_store\.put", r"\.set_memory\(", r"memory_store\[",
        r"embeddings\.add", r"collection\.insert",
    ]
    governance_words = {
        "authorized", "sanitize", "validate", "governance", "policy",
        "approved", "signed", "verified", "audit_log", "log_memory_write",
        "safe_memory", "governed_write"
    }

    for i, line in enumerate(lines):
        for pat in write_patterns:
            if re.search(pat, line, re.IGNORECASE):
                # Check surrounding 5 lines for governance keywords
                start = max(0, i - 3)
                end = min(len(lines), i + 3)
                context = " ".join(lines[start:end]).lower()
                if not any(g in context for g in governance_words):
                    findings.append((
                        i + 1,
                        f"Memory write without governance wrapper: {line.strip()[:60]}"
                    ))
    return findings


def _check_n8n_expression_injection(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    S1.7 — No-Code / Low-Code Platform Security
    Detect n8n expression injection risk: user-controlled data in template expressions
    passed directly to AI nodes.
    """
    findings = []
    # n8n expressions that pull from trigger/user input
    dangerous_sources = [
        r'\$json\.chatInput', r'\$json\.message', r'\$json\.userInput',
        r'\$json\.body', r'\$json\.query', r'\$input\.item\.json',
        r'\{\{\s*\$json\.',
    ]
    # n8n AI/agent node types that indicate an LLM sink
    ai_node_markers = [
        r'"type":\s*"@n8n/n8n-nodes-langchain', r'"type":\s*"n8n-nodes-base.openAi',
        r'"type":\s*"@n8n/n8n-nodes-base.agent', r'"nodeType".*[Aa]i',
        r'"nodeType".*[Ll][Ll][Mm]',
    ]

    if not filepath.endswith(".json"):
        return []

    has_ai_node = any(re.search(m, content) for m in ai_node_markers)
    if not has_ai_node:
        return []

    for i, line in enumerate(lines):
        for src in dangerous_sources:
            if re.search(src, line):
                findings.append((
                    i + 1,
                    f"n8n expression injection risk — user input in AI node: {line.strip()[:60]}"
                ))
    return findings


def _check_pickle_model_loading(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    P1.T1.9 — Supply Chain Artifact Validation
    Detect unsafe model loading patterns (pickle deserialization without verification).
    """
    findings = []
    unsafe_load_patterns = [
        r"pickle\.load\s*\(", r"torch\.load\s*\((?!.*weights_only\s*=\s*True)",
        r"joblib\.load\s*\(", r"numpy\.load\s*\(.*allow_pickle\s*=\s*True",
    ]
    safe_context_words = {"sha256", "checksum", "verify", "signature", "hash", "trusted"}

    for i, line in enumerate(lines):
        for pat in unsafe_load_patterns:
            if re.search(pat, line, re.IGNORECASE):
                context = " ".join(lines[max(0, i-2):i+3]).lower()
                if not any(w in context for w in safe_context_words):
                    findings.append((
                        i + 1,
                        f"Unsafe model deserialization without integrity check: {line.strip()[:60]}"
                    ))
    return findings


# ── Rule Definitions ──────────────────────────────────────────────────────────

P1_RULES: list[Rule] = [

    # ── P1.T1.x Sanitize ─────────────────────────────────────────────────────

    # Secret detection (P1.T1.4_ADV)
    Rule(
        control_id="P1.T1.4_ADV",
        severity="CRITICAL",
        description="Hardcoded OpenAI API key detected.",
        remediation="Remove from code. Use environment variables and a secrets manager. Never expose in prompts or logs.",
        pattern=r"sk-[a-zA-Z0-9]{32,}",
    ),
    Rule(
        control_id="P1.T1.4_ADV",
        severity="CRITICAL",
        description="Hardcoded GitHub personal access token detected.",
        remediation="Rotate immediately. Store in secrets manager. Use short-lived tokens with minimum scope.",
        pattern=r"ghp_[a-zA-Z0-9]{36}",
    ),
    Rule(
        control_id="P1.T1.4_ADV",
        severity="CRITICAL",
        description="Hardcoded Anthropic API key detected.",
        remediation="Rotate immediately. Use environment variables. Never embed in prompts or logs.",
        pattern=r"sk-ant-[a-zA-Z0-9\-]{40,}",
    ),
    Rule(
        control_id="P1.T1.4_ADV",
        severity="CRITICAL",
        description="AWS access key ID detected.",
        remediation="Rotate immediately. Use IAM roles and instance profiles instead of long-lived keys.",
        pattern=r"AKIA[0-9A-Z]{16}",
    ),
    Rule(
        control_id="P1.T1.4_ADV",
        severity="CRITICAL",
        description="Private key block detected in source file.",
        remediation="Remove immediately. Private keys must never be committed to source control.",
        pattern=r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    ),
    Rule(
        control_id="P1.T1.4_ADV",
        severity="CRITICAL",
        description="Hardcoded Hugging Face token detected.",
        remediation="Rotate token. Use environment variable HF_TOKEN instead.",
        pattern=r"hf_[a-zA-Z0-9]{34,}",
    ),
    Rule(
        control_id="P1.T1.4_ADV",
        severity="HIGH",
        description="API key or token assigned directly to a variable.",
        remediation="Move to environment variable or secrets manager. Reference via os.getenv().",
        pattern=r'(?i)(api_key|api_token|secret_key|access_token)\s*=\s*["\'][^"\']{16,}["\']',
    ),

    # Prompt injection defense (P1.T1.2)
    Rule(
        control_id="P1.T1.2",
        severity="HIGH",
        description="User input directly concatenated into LLM prompt without sanitization.",
        remediation="Apply P1.T1.2 sanitization before including user input in prompts. "
                    "Use a validated prompt template rather than string concatenation.",
        pattern=r'prompt\s*[+=]\s*.*?(user_input|query|message|user_message|request)',
        file_exts=(".py", ".js", ".ts"),
    ),
    Rule(
        control_id="P1.T1.2",
        severity="HIGH",
        description="f-string prompt with unvalidated variable — potential injection surface.",
        remediation="Validate and sanitize all variables before embedding in prompts. "
                    "Use separate system and user context boundaries.",
        pattern=r'f["\'].*\{(user_|query|message|input|request|chat)',
        file_exts=(".py",),
    ),

    # PII in LLM context (P1.T1.5)
    Rule(
        control_id="P1.T1.5",
        severity="HIGH",
        description="Potential SSN pattern in source — verify PII is not flowing into LLM context.",
        remediation="Apply P1.T1.5 PII masking before any data reaches the model. "
                    "Use a DLP tool to scan inputs and outputs.",
        pattern=r"\b\d{3}-\d{2}-\d{4}\b",
        skip_comments=False,
    ),
    Rule(
        control_id="P1.T1.5",
        severity="HIGH",
        description="16-digit pattern that may be a credit card number — verify not in LLM context.",
        remediation="Apply PCI-DSS compliant tokenization. Never pass card data to an LLM.",
        pattern=r"\b(?:\d[ -]?){15,16}\d\b",
        skip_comments=False,
    ),

    # Encoding attacks (P1.T1.8)
    Rule(
        control_id="P1.T1.8",
        severity="MEDIUM",
        description="Unicode normalization not enforced — homoglyph injection risk.",
        remediation="Apply NFKC normalization (unicodedata.normalize) to all inputs before processing. "
                    "Detect and reject zero-width characters and invisible Unicode.",
        pattern=r"unicodedata\.normalize",
        skip_comments=True,
        # This is a POSITIVE pattern — we flag if it's ABSENT. Handled specially in scanner.
        # For now flag files that use LLM inputs without normalization - see structural check.
    ),

    # Supply chain artifact validation (P1.T1.9)
    Rule(
        control_id="P1.T1.9",
        severity="CRITICAL",
        description="Unsafe model deserialization — pickle/torch.load without integrity check.",
        remediation="Apply P1.T1.9: verify SHA-256 checksum before loading. "
                    "Use torch.load with weights_only=True for PyTorch models.",
        check_fn=_check_pickle_model_loading,
        file_exts=(".py",),
    ),

    # Indirect injection (P1.T1.10) — NEW v3.0
    Rule(
        control_id="P1.T1.10",
        severity="CRITICAL",
        description="External content (email, retrieved document, tool output, web page) "
                    "may reach LLM context without sanitization — indirect injection surface.",
        remediation="Apply P1.T1.10: treat every non-prompt input channel as a sanitization surface. "
                    "Sanitize retrieved content with the same rigor as direct user input.",
        check_fn=_check_indirect_injection,
        file_exts=(".py", ".js", ".ts"),
    ),

    # ── P1.T2.x Isolate ───────────────────────────────────────────────────────

    Rule(
        control_id="P1.T2.1",
        severity="HIGH",
        description="subprocess with shell=True — shell injection risk if any argument is user-controlled.",
        remediation="Use shell=False with a list of arguments. Validate all inputs before subprocess calls.",
        pattern=r"shell\s*=\s*True",
        file_exts=(".py",),
    ),
    Rule(
        control_id="P1.T2.1",
        severity="HIGH",
        description="eval() usage — code injection risk, especially with any external data.",
        remediation="Remove eval(). Use ast.literal_eval() for safe deserialization of literals, "
                    "or a proper parser for structured data.",
        pattern=r"\beval\s*\(",
        file_exts=(".py", ".js", ".ts"),
    ),
    Rule(
        control_id="P1.T2.1",
        severity="HIGH",
        description="exec() usage — arbitrary code execution risk.",
        remediation="Remove exec(). If dynamic code execution is required, use a sandboxed subprocess "
                    "with strict resource limits rather than the main process.",
        pattern=r"\bexec\s*\(",
        file_exts=(".py",),
    ),
    Rule(
        control_id="P1.T2.1",
        severity="HIGH",
        description="os.system() call — command injection risk if argument includes user input.",
        remediation="Replace with subprocess.run() using a list of arguments and shell=False.",
        pattern=r"\bos\.system\s*\(",
        file_exts=(".py",),
    ),
    Rule(
        control_id="P1.T2.2",
        severity="MEDIUM",
        description="Service binding to all interfaces (0.0.0.0) — unintended network exposure.",
        remediation="Bind to 127.0.0.1 for local-only services. Use a reverse proxy (Caddy, Nginx) "
                    "to handle public-facing TLS termination.",
        pattern=r"0\.0\.0\.0",
        file_exts=(".py", ".js", ".ts", ".yaml", ".json"),
    ),
    Rule(
        control_id="P1.T2.9",
        severity="HIGH",
        description="API key or secret in apparent plain-text assignment — credential exposure risk.",
        remediation="Move to environment variables or a secrets manager. "
                    "Rotate any key that has been in source control.",
        pattern=r'(?i)(password|passwd|secret|token|credential)\s*=\s*["\'][^"\']{8,}["\']',
    ),

    # ── S1.3-S1.7 New v3.0 Controls ──────────────────────────────────────────

    # S1.5 Memory write governance (NEW v3.0)
    Rule(
        control_id="S1.5",
        severity="CRITICAL",
        description="Vector DB or agent memory write without governance wrapper — "
                    "no evidence of authorization, sanitization, or audit logging.",
        remediation="Apply S1.5: every write to persistent agent memory must be authorized, "
                    "sanitized with input-equivalent rigor, and logged to an append-only audit store.",
        check_fn=_check_memory_write_governance,
        file_exts=(".py", ".js", ".ts"),
    ),

    # S1.7 No-code platform security (NEW v3.0)
    Rule(
        control_id="S1.7",
        severity="CRITICAL",
        description="n8n workflow: user-controlled data in expression flows to an AI/LLM node "
                    "without sanitization — indirect injection surface (CVE-2026-25049 class).",
        remediation="Apply S1.7: insert a sanitization Code node before every AI Agent node. "
                    "Block known injection patterns and enforce input length limits.",
        check_fn=_check_n8n_expression_injection,
        file_exts=(".json",),
    ),
    Rule(
        control_id="S1.7",
        severity="HIGH",
        description="n8n or automation credential node detected — verify credential scope is minimal.",
        remediation="Apply S1.7: restrict automation workflow credentials to minimum required scope. "
                    "Rotate on a defined cadence. Never use admin credentials in AI workflows.",
        pattern=r'"type":\s*"n8n-nodes-base\.httpRequest.*credentials"',
        file_exts=(".json",),
    ),
]
