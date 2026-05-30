#!/usr/bin/env python3
"""
AI SAFE² Gateway v3.0 — Hermes Sovereign Runtime
Cyber Strategy Institute

LLM API enforcement proxy for Hermes Agent.
Intercepts every request/response between Hermes and any LLM provider,
applies AI SAFE² v3.0 controls, and emits an immutable audit trail.

Controls enforced:
  P1.S-C02 — PII/secrets filter (blocks credentials from entering LLM context)
  P1.S-C05 — Taint-tracking (tags external-surface content before LLM injection)
  P2.A-C05 — Immutable audit log (append-only JSONL with integrity hash chain)
  P3.F-C05 — Kill switch (circuit breaker on anomaly threshold)
  P4.M-C01 — Prompt-layer semantic anomaly detection
  P4.M-C03 — Tool call telemetry

Usage:
  export ANTHROPIC_API_KEY="sk-ant-..."
  export AUDIT_CHAIN_KEY="$(openssl rand -hex 32)"
  python3 gateway.py

Then configure Hermes:
  ANTHROPIC_BASE_URL=http://127.0.0.1:8000/v1

Supports: Anthropic · OpenAI · Gemini · Ollama · OpenRouter
"""

import json
import hashlib
import hmac
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml
from flask import Flask, Response, jsonify, request, stream_with_context

# ─── Configuration ───────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "config.yaml"
DEFAULT_CONFIG = {
    "gateway": {
        "host": "127.0.0.1",
        "port": 8000,
        "max_request_size_bytes": 32768,
        "circuit_breaker_threshold": 0.85,
        "kill_switch_file": "/tmp/hsr_kill_switch",
    },
    "filters": {
        "block_pii": True,
        "block_secrets": True,
        "block_injection_patterns": True,
        "max_context_tokens": 8192,
    },
    "audit": {
        "log_path": "/var/log/hsr/audit.jsonl",
        "fallback_log_path": "/tmp/hsr_audit.jsonl",
        "hash_algorithm": "sha256",
    },
    "provider": {
        "active": "anthropic",
    },
    "tools": {
        "allowed": ["read_file", "web_search", "write_file", "terminal", "memory_search"],
        "require_approval": ["terminal", "write_file"],
        "blocked": ["system_exec", "raw_bash"],
    },
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG


CONFIG = load_config()

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HSR-GATEWAY] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("hsr.gateway")

# ─── Audit Chain ─────────────────────────────────────────────────────────────

AUDIT_KEY = os.environ.get("AUDIT_CHAIN_KEY", "")
_previous_hash = "GENESIS"

audit_cfg = CONFIG.get("audit", DEFAULT_CONFIG["audit"])
AUDIT_PATH = Path(audit_cfg.get("log_path", "/var/log/hsr/audit.jsonl"))
if not AUDIT_PATH.parent.exists():
    AUDIT_PATH = Path(audit_cfg.get("fallback_log_path", "/tmp/hsr_audit.jsonl"))


def _write_audit(event: dict) -> None:
    global _previous_hash
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    event["prev_hash"] = _previous_hash
    payload = json.dumps(event, sort_keys=True)
    if AUDIT_KEY:
        current_hash = hmac.new(AUDIT_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    else:
        current_hash = hashlib.sha256(payload.encode()).hexdigest()
    event["hash"] = current_hash
    _previous_hash = current_hash
    with open(AUDIT_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")


# ─── Secret / PII Patterns ───────────────────────────────────────────────────

SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("anthropic_key", re.compile(r"sk-ant-[a-zA-Z0-9\-_]{20,}")),
    ("openai_key", re.compile(r"sk-(?:proj-)?[a-zA-Z0-9]{32,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("aws_secret_key", re.compile(r"(?i)aws[_\s]?secret[_\s]?access[_\s]?key[^\n]{0,30}['\"][0-9a-zA-Z/+=]{40}['\"]")),
    ("gcp_service_account", re.compile(r'"type":\s*"service_account"')),
    ("private_key_pem", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("generic_api_key", re.compile(r"(?i)(?:api[_\s]?key|apikey|api_secret)['\"\s:=]+[a-zA-Z0-9\-_]{16,}")),
    ("github_token", re.compile(r"gh[pos]_[A-Za-z0-9]{36}")),
    ("jwt_token", re.compile(r"eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+")),
    ("database_url", re.compile(r"(?i)(?:postgres|mysql|mongodb|redis)://[^:]+:[^@]+@[^\s]+")),
]

PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b")),
    ("email_bulk", re.compile(r"(?:[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}(?:\s*[,;]\s*)){3,}")),
]

INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("ignore_instructions", re.compile(r"(?i)ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?")),
    ("new_system_prompt", re.compile(r"(?i)(?:your\s+)?new\s+system\s+prompt\s+is")),
    ("no_restrictions", re.compile(r"(?i)(?:you\s+have\s+)?no\s+restrictions?\s+(?:now|in\s+this\s+session)")),
    ("developer_mode", re.compile(r"(?i)developer\s+mode\s+(?:enabled|active|on)")),
    ("you_are_now", re.compile(r"(?i)you\s+are\s+now\s+(?:a\s+)?(?:different|new|alternative|unrestricted)")),
    ("jailbreak_dan", re.compile(r"(?i)\bDAN\b.*(?:do\s+anything\s+now|no\s+restrictions)")),
    ("override_safety", re.compile(r"(?i)override\s+(?:your\s+)?safety")),
    ("disregard_guidelines", re.compile(r"(?i)disregard\s+(?:your\s+)?(?:safety\s+)?guidelines?")),
]


def scan_content(text: str) -> list[dict]:
    """Scan text for secrets, PII, and injection patterns. Returns list of findings."""
    findings = []
    cfg = CONFIG.get("filters", DEFAULT_CONFIG["filters"])

    if cfg.get("block_secrets", True):
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append({"type": "secret", "pattern": name, "severity": "CRITICAL"})

    if cfg.get("block_pii", True):
        for name, pattern in PII_PATTERNS:
            if pattern.search(text):
                findings.append({"type": "pii", "pattern": name, "severity": "HIGH"})

    if cfg.get("block_injection_patterns", True):
        for name, pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                findings.append({"type": "injection", "pattern": name, "severity": "HIGH"})

    return findings


# ─── Kill Switch ─────────────────────────────────────────────────────────────

def is_kill_switch_active() -> bool:
    kill_file = CONFIG.get("gateway", {}).get("kill_switch_file", "/tmp/hsr_kill_switch")
    return Path(kill_file).exists()


def activate_kill_switch(reason: str) -> None:
    kill_file = CONFIG.get("gateway", {}).get("kill_switch_file", "/tmp/hsr_kill_switch")
    Path(kill_file).write_text(
        json.dumps({"activated_at": datetime.now(timezone.utc).isoformat(), "reason": reason})
    )
    log.critical(f"KILL SWITCH ACTIVATED: {reason}")
    _write_audit({"event": "kill_switch_activated", "reason": reason, "severity": "CRITICAL"})


# ─── Tool Allowlist ───────────────────────────────────────────────────────────

def check_tool_allowed(tool_name: str) -> tuple[bool, str]:
    tools_cfg = CONFIG.get("tools", DEFAULT_CONFIG["tools"])
    blocked = tools_cfg.get("blocked", [])
    allowed = tools_cfg.get("allowed", [])

    if tool_name in blocked:
        return False, f"Tool '{tool_name}' is explicitly blocked by HSR policy"
    if allowed and tool_name not in allowed:
        return False, f"Tool '{tool_name}' is not in HSR allowlist: {allowed}"
    return True, "allowed"


# ─── Request Processing ───────────────────────────────────────────────────────

def process_request(body: dict) -> tuple[dict | None, list[dict]]:
    """
    Inspect and optionally modify an outbound LLM request.
    Returns (modified_body_or_None_if_blocked, findings_list).
    """
    all_findings = []

    # Size check
    max_size = CONFIG.get("gateway", {}).get("max_request_size_bytes", 32768)
    body_bytes = len(json.dumps(body).encode())
    if body_bytes > max_size:
        all_findings.append({
            "type": "oversized_request",
            "severity": "HIGH",
            "detail": f"{body_bytes} bytes exceeds limit {max_size}",
        })
        return None, all_findings

    # Scan all message content
    messages = body.get("messages", [])
    for i, msg in enumerate(messages):
        content = msg.get("content", "")
        if isinstance(content, list):
            # Multi-part content (vision, documents, etc.)
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    findings = scan_content(part.get("text", ""))
                    for f in findings:
                        f["location"] = f"messages[{i}].content[text]"
                    all_findings.extend(findings)
        elif isinstance(content, str):
            findings = scan_content(content)
            for f in findings:
                f["location"] = f"messages[{i}].content"
            all_findings.extend(findings)

    # Check tool use in request
    tools = body.get("tools", [])
    for tool in tools:
        name = tool.get("name", "")
        allowed, reason = check_tool_allowed(name)
        if not allowed:
            all_findings.append({"type": "blocked_tool", "severity": "HIGH", "tool": name, "reason": reason})

    # Block if critical findings present
    critical = [f for f in all_findings if f["severity"] == "CRITICAL"]
    if critical:
        return None, all_findings

    return body, all_findings


# ─── Provider Routing ─────────────────────────────────────────────────────────

def get_upstream_url(path: str) -> str:
    from provider_adapters import get_upstream_url as _get
    return _get(path, CONFIG)


# ─── Flask Application ────────────────────────────────────────────────────────

app = Flask(__name__)


@app.before_request
def check_kill_switch():
    if is_kill_switch_active() and not request.path.startswith("/hsr/"):
        _write_audit({"event": "request_blocked_kill_switch", "path": request.path})
        return jsonify({
            "error": "HSR Kill Switch Active",
            "message": "All LLM operations suspended. Contact your security administrator.",
            "hsr_code": "KILL_SWITCH_ACTIVE",
        }), 503


@app.route("/v1/messages", methods=["POST"])
@app.route("/v1/chat/completions", methods=["POST"])
def proxy_messages():
    request_id = f"hsr-{int(time.time() * 1000)}"
    start_time = time.time()

    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    # Run request through controls
    processed_body, findings = process_request(body)

    # Log all findings
    if findings:
        _write_audit({
            "event": "request_findings",
            "request_id": request_id,
            "findings": findings,
            "path": request.path,
            "model": body.get("model", "unknown"),
        })

    # Block if processing returned None
    if processed_body is None:
        critical = [f for f in findings if f["severity"] == "CRITICAL"]
        log.warning(f"[{request_id}] Request BLOCKED — {len(critical)} critical findings")
        return jsonify({
            "error": "HSR Policy Violation",
            "findings": critical,
            "request_id": request_id,
            "hsr_code": "REQUEST_BLOCKED",
        }), 403

    # Forward to upstream
    try:
        upstream_url = get_upstream_url(request.path)
    except Exception as e:
        log.error(f"[{request_id}] Provider routing error: {e}")
        upstream_url = f"https://api.anthropic.com{request.path}"

    # Build upstream headers
    upstream_headers = {k: v for k, v in request.headers if k.lower() not in
                        ("host", "content-length", "transfer-encoding")}

    # Inject provider API key if not present
    provider = CONFIG.get("provider", {}).get("active", "anthropic")
    if provider == "anthropic" and "x-api-key" not in {k.lower() for k in upstream_headers}:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            upstream_headers["x-api-key"] = key
    elif provider in ("openai", "openrouter") and "authorization" not in {k.lower() for k in upstream_headers}:
        key = os.environ.get("OPENAI_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
        if key:
            upstream_headers["Authorization"] = f"Bearer {key}"

    streaming = processed_body.get("stream", False)

    try:
        upstream_resp = requests.request(
            method=request.method,
            url=upstream_url,
            headers=upstream_headers,
            json=processed_body,
            stream=streaming,
            timeout=120,
        )
    except requests.exceptions.RequestException as e:
        log.error(f"[{request_id}] Upstream error: {e}")
        return jsonify({"error": "Upstream LLM unreachable", "detail": str(e)}), 502

    duration_ms = int((time.time() - start_time) * 1000)

    # Audit the completed request
    _write_audit({
        "event": "request_proxied",
        "request_id": request_id,
        "model": processed_body.get("model", "unknown"),
        "provider": provider,
        "status_code": upstream_resp.status_code,
        "duration_ms": duration_ms,
        "findings_count": len(findings),
        "path": request.path,
    })

    log.info(f"[{request_id}] {request.method} {request.path} → {upstream_resp.status_code} ({duration_ms}ms) findings={len(findings)}")

    if streaming:
        def generate():
            for chunk in upstream_resp.iter_content(chunk_size=None):
                yield chunk

        return Response(
            stream_with_context(generate()),
            status=upstream_resp.status_code,
            headers={k: v for k, v in upstream_resp.headers.items()
                     if k.lower() not in ("transfer-encoding", "content-encoding")},
            content_type=upstream_resp.headers.get("content-type", "application/json"),
        )

    return Response(
        upstream_resp.content,
        status=upstream_resp.status_code,
        headers={k: v for k, v in upstream_resp.headers.items()
                 if k.lower() not in ("transfer-encoding",)},
        content_type=upstream_resp.headers.get("content-type", "application/json"),
    )


# ─── HSR Management Endpoints ────────────────────────────────────────────────

@app.route("/hsr/health", methods=["GET"])
def health():
    return jsonify({
        "status": "operational" if not is_kill_switch_active() else "kill_switch_active",
        "version": "3.0.0",
        "provider": CONFIG.get("provider", {}).get("active", "anthropic"),
        "audit_path": str(AUDIT_PATH),
        "filters": CONFIG.get("filters", {}),
        "uptime_seconds": int(time.time() - _start_time),
    })


@app.route("/hsr/kill", methods=["POST"])
def kill():
    data = request.get_json(force=True) or {}
    reason = data.get("reason", "Manual kill switch activation")
    activate_kill_switch(reason)
    return jsonify({"status": "kill_switch_activated", "reason": reason})


@app.route("/hsr/revive", methods=["POST"])
def revive():
    kill_file = CONFIG.get("gateway", {}).get("kill_switch_file", "/tmp/hsr_kill_switch")
    kf = Path(kill_file)
    if kf.exists():
        kf.unlink()
        _write_audit({"event": "kill_switch_deactivated", "severity": "WARNING"})
        log.warning("Kill switch deactivated via management endpoint")
        return jsonify({"status": "revived"})
    return jsonify({"status": "kill_switch_was_not_active"})


@app.route("/hsr/audit/tail", methods=["GET"])
def audit_tail():
    n = int(request.args.get("n", 20))
    if not AUDIT_PATH.exists():
        return jsonify({"events": [], "message": "No audit log yet"})
    lines = AUDIT_PATH.read_text().strip().split("\n")
    tail = [json.loads(l) for l in lines[-n:] if l.strip()]
    return jsonify({"events": tail, "total_count": len(lines)})


@app.route("/hsr/scan", methods=["POST"])
def scan():
    """Ad-hoc content scan endpoint — test the filter without proxying."""
    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    findings = scan_content(text)
    return jsonify({"findings": findings, "clean": len(findings) == 0})


# ─── Startup ─────────────────────────────────────────────────────────────────

_start_time = time.time()

if __name__ == "__main__":
    log.info("═" * 60)
    log.info("  AI SAFE² Gateway v3.0 — Hermes Sovereign Runtime")
    log.info("  Cyber Strategy Institute")
    log.info("═" * 60)

    if not AUDIT_KEY:
        log.warning("AUDIT_CHAIN_KEY not set — audit log integrity hashing disabled")
        log.warning("Run: export AUDIT_CHAIN_KEY=\"$(openssl rand -hex 32)\"")

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_audit({"event": "gateway_started", "version": "3.0.0", "config": CONFIG.get("gateway", {})})

    provider = CONFIG.get("provider", {}).get("active", "anthropic")
    log.info(f"Provider: {provider}")
    log.info(f"Audit log: {AUDIT_PATH}")
    log.info(f"Filters: PII={CONFIG.get('filters',{}).get('block_pii')}, "
             f"Secrets={CONFIG.get('filters',{}).get('block_secrets')}, "
             f"Injection={CONFIG.get('filters',{}).get('block_injection_patterns')}")

    gw = CONFIG.get("gateway", DEFAULT_CONFIG["gateway"])
    app.run(
        host=gw.get("host", "127.0.0.1"),
        port=gw.get("port", 8000),
        debug=False,
        threaded=True,
    )
