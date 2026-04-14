"""
provider_adapters.py — AI SAFE² Gateway v3.0
Multi-provider adapter layer with NEXUS-A2A compatibility hooks.

Supported providers:
  anthropic   — Anthropic Claude (api.anthropic.com)
  openai      — OpenAI ChatGPT / Codex (api.openai.com)
  gemini      — Google Gemini (generativelanguage.googleapis.com)
  ollama      — Local models via Ollama (localhost or custom host)
  openrouter  — OpenRouter unified API (openrouter.ai)

NEXUS-A2A Compatibility (v0.2):
  - Envelope detection: X-NEXUS-* headers preserved and passed through
  - Identity fields: nexus_agent_id, nexus_delegation_chain extracted and logged
  - A2A detection upgraded to include NEXUS canonical indicators
  - No NEXUS implementation here — hooks are forward-compatible with NEXUS v0.2 release

Design principle: pass-through with provider-aware adapters.
  - Client sends requests in provider's native format
  - Gateway enforces on the internal NormalizedRequest
  - Adapter translates auth headers and extracts enforcement-relevant fields
  - Original payload forwarded untouched downstream
  - Response adapter extracts content for scanning, returns original response to client

Usage:
  adapter = get_adapter(provider_name, config)
  normalized = adapter.normalize_request(headers, body_dict)
  response   = adapter.forward(raw_body, timeout)
  is_clean, reason = adapter.scan_response(response_body_bytes)
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import requests as http_requests

logger = logging.getLogger(__name__)

GATEWAY_VERSION = "3.0.0"

# ── NEXUS-A2A v0.2 header and field constants ─────────────────────────────────
# These are the canonical NEXUS headers/fields as specified in NEXUS-A2A v0.2.
# The gateway preserves and logs these when present.
# Full enforcement (signature verification, DID resolution, delegation chain
# validation) is a NEXUS runtime concern — not implemented here.

NEXUS_HEADERS = {
    "x-nexus-agent-id",         # AIM DID or local workload identity
    "x-nexus-session-id",       # NEXUS session UUID
    "x-nexus-delegation-chain", # Base64-encoded delegation chain JSON
    "x-nexus-nonce",            # Replay-protection nonce
    "x-nexus-signature",        # Ed25519 payload signature
    "x-nexus-jurisdiction",     # Sovereignty zone tag
    "x-nexus-profile",          # NEXUS profile tier (simple/standard/full)
    "x-nexus-version",          # Protocol version
}

# NEXUS-aware A2A indicators — extends base AI SAFE² A2A detection
# Includes NEXUS canonical message types from v0.2 spec
NEXUS_A2A_INDICATORS = [
    # Existing AI SAFE² indicators
    "orchestrat", "subagent", "delegate to", "forward to agent",
    "as the orchestrator", "acting as agent", "i am the supervisor",
    "agent-to-agent", "tool_result", "from: agent", "x-agent-id",
    "multi-agent",
    # NEXUS-A2A v0.2 canonical indicators
    "nexus-a2a", "nexus_agent", "aim_did", "nexus_session",
    "delegation_chain", "nexus_mandate", "nexus_profile",
    "workload_attestation", "spiffe://", "spire-agent",
    "nor_receipt",              # NEXUS Output Receipt
    "nexus_swarm",              # Swarm governance messages
    "nexus_dissolution",        # Swarm dissolution mandate
]

# ── Normalized internal request ───────────────────────────────────────────────

@dataclass
class NormalizedRequest:
    """
    Provider-agnostic representation of a request for enforcement purposes.
    The gateway enforces on this object. Original payload is forwarded untouched.

    NEXUS fields are populated when NEXUS headers are present.
    They are logged and passed through; not enforced at this layer.
    """
    # Core enforcement fields
    user_id: str = "unknown"
    messages: list[dict] = field(default_factory=list)
    tools: list[dict] = field(default_factory=list)
    system_prompt: str = ""
    model: str = ""
    provider: str = ""

    # NEXUS-A2A v0.2 compatibility fields
    nexus_agent_id: Optional[str] = None        # x-nexus-agent-id
    nexus_session_id: Optional[str] = None      # x-nexus-session-id
    nexus_delegation_chain: Optional[str] = None # x-nexus-delegation-chain
    nexus_jurisdiction: Optional[str] = None    # x-nexus-jurisdiction
    nexus_profile: Optional[str] = None         # x-nexus-profile
    nexus_version: Optional[str] = None         # x-nexus-version
    nexus_headers_present: bool = False          # True if any NEXUS header detected

    # Raw fields for risk scoring passthrough
    raw_body_dict: dict = field(default_factory=dict)

    def to_risk_input(self) -> dict:
        """Return a dict shaped for calculate_composite_risk()."""
        return {
            "messages": self.messages,
            "tools":    self.tools,
            "system":   self.system_prompt,
        }


# ── Base adapter ──────────────────────────────────────────────────────────────

class ProviderAdapter(ABC):
    """
    Base class for all provider adapters.
    Subclasses implement: normalize_request(), build_headers(), endpoint_url,
    and extract_response_content() for response scanning.
    """

    def __init__(self, config: dict):
        self._cfg = config

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def endpoint_url(self) -> str: ...

    @abstractmethod
    def build_headers(self) -> dict[str, str]:
        """Build auth and protocol headers for upstream request."""
        ...

    @abstractmethod
    def normalize_request(self, headers: dict, body: dict) -> NormalizedRequest:
        """
        Extract enforcement-relevant fields from provider-native request body.
        Also extracts NEXUS headers if present.
        """
        ...

    @abstractmethod
    def extract_response_content(self, response_body: bytes) -> list[dict]:
        """
        Extract content blocks from provider response for scanning.
        Returns a list of dicts with at minimum: {"type": str, "text"/"input": ...}
        Normalized to Anthropic content block shape for the scanner.
        """
        ...

    # ── NEXUS header extraction (shared by all adapters) ──────────────────────

    def extract_nexus_fields(self, headers: dict) -> dict:
        """
        Extract NEXUS-A2A v0.2 fields from request headers.
        Returns dict of nexus_* fields. Empty if no NEXUS headers present.
        """
        lower_headers = {k.lower(): v for k, v in headers.items()}
        nexus = {}
        present = False
        for h in NEXUS_HEADERS:
            if h in lower_headers:
                nexus[h.replace("x-nexus-", "nexus_").replace("-", "_")] = lower_headers[h]
                present = True
        nexus["nexus_headers_present"] = present
        return nexus

    # ── Shared forward method ─────────────────────────────────────────────────

    def forward(self, raw_body: bytes, timeout: int = 60) -> http_requests.Response:
        """Forward raw request bytes to upstream. Returns raw response."""
        headers = self.build_headers()
        headers["content-type"] = "application/json"
        headers["x-forwarded-by"] = f"aisafe2-gateway/{GATEWAY_VERSION}"

        logger.debug("Forwarding to %s [%s]", self.provider_name, self.endpoint_url)
        return http_requests.post(
            self.endpoint_url,
            headers=headers,
            data=raw_body,
            timeout=timeout,
        )

    def scan_response(self, response_body: bytes) -> tuple[bool, str]:
        """
        Scan provider response for exfil and injection.
        Returns (is_clean, reason).
        Normalizes provider content to Anthropic block shape for unified scanner.
        """
        try:
            blocks = self.extract_response_content(response_body)
        except Exception as e:
            logger.warning("Response extraction failed for %s: %s", self.provider_name, e)
            return True, "extraction-failed-skipped"

        return _scan_normalized_blocks(blocks)


# ── Anthropic adapter ─────────────────────────────────────────────────────────

class AnthropicAdapter(ProviderAdapter):

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def endpoint_url(self) -> str:
        return self._cfg.get("endpoint", "https://api.anthropic.com/v1/messages")

    def build_headers(self) -> dict[str, str]:
        return {
            "x-api-key":         self._cfg.get("api_key", ""),
            "anthropic-version": self._cfg.get("version", "2023-06-01"),
        }

    def normalize_request(self, headers: dict, body: dict) -> NormalizedRequest:
        nexus = self.extract_nexus_fields(headers)
        return NormalizedRequest(
            provider=self.provider_name,
            model=body.get("model", ""),
            messages=body.get("messages", []),
            tools=body.get("tools", []),
            system_prompt=body.get("system", ""),
            raw_body_dict=body,
            **nexus,
        )

    def extract_response_content(self, response_body: bytes) -> list[dict]:
        data = json.loads(response_body)
        return data.get("content", [])


# ── OpenAI adapter (ChatGPT / Codex) ─────────────────────────────────────────

class OpenAIAdapter(ProviderAdapter):

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def endpoint_url(self) -> str:
        return self._cfg.get("endpoint", "https://api.openai.com/v1/chat/completions")

    def build_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._cfg.get('api_key', '')}",
        }
        if org := self._cfg.get("organization"):
            headers["OpenAI-Organization"] = org
        return headers

    def normalize_request(self, headers: dict, body: dict) -> NormalizedRequest:
        nexus = self.extract_nexus_fields(headers)
        # OpenAI uses "messages" same key; "tools" same key; "system" is a message role
        system_prompt = ""
        messages = []
        for msg in body.get("messages", []):
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                messages.append(msg)

        # Normalize tools: OpenAI function/tool format → enforcement-compatible
        tools = []
        for t in body.get("tools", []):
            if isinstance(t, dict):
                fn = t.get("function", t)
                tools.append({"name": fn.get("name", ""), "description": fn.get("description", "")})

        return NormalizedRequest(
            provider=self.provider_name,
            model=body.get("model", ""),
            messages=messages,
            tools=tools,
            system_prompt=system_prompt,
            raw_body_dict=body,
            **nexus,
        )

    def extract_response_content(self, response_body: bytes) -> list[dict]:
        """Normalize OpenAI choices → Anthropic-style content blocks for scanner."""
        data = json.loads(response_body)
        blocks = []
        for choice in data.get("choices", []):
            msg = choice.get("message", {})
            if text := msg.get("content"):
                blocks.append({"type": "text", "text": text})
            for tc in msg.get("tool_calls", []):
                fn = tc.get("function", {})
                try:
                    input_data = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    input_data = {"raw": fn.get("arguments", "")}
                blocks.append({
                    "type":  "tool_use",
                    "name":  fn.get("name", "unknown"),
                    "input": input_data,
                })
        return blocks


# ── Gemini adapter ────────────────────────────────────────────────────────────

class GeminiAdapter(ProviderAdapter):

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def endpoint_url(self) -> str:
        model   = self._cfg.get("model", "gemini-1.5-pro")
        api_key = self._cfg.get("api_key", "")
        base    = self._cfg.get(
            "endpoint",
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        )
        return f"{base}?key={api_key}" if "?" not in base else base

    def build_headers(self) -> dict[str, str]:
        # Gemini auth is via query param (api_key appended to URL above)
        # x-goog-api-key header also supported as alternative
        return {
            "x-goog-api-key": self._cfg.get("api_key", ""),
        }

    def normalize_request(self, headers: dict, body: dict) -> NormalizedRequest:
        nexus = self.extract_nexus_fields(headers)
        # Gemini format: {"contents": [{"role": "user", "parts": [{"text": "..."}]}]}
        messages = []
        system_prompt = ""

        for content in body.get("contents", []):
            role = content.get("role", "user")
            text = " ".join(
                p.get("text", "") for p in content.get("parts", [])
                if isinstance(p, dict) and "text" in p
            )
            if role == "system":
                system_prompt = text
            else:
                messages.append({"role": role, "content": text})

        # Gemini tools: functionDeclarations
        tools = []
        for td in body.get("tools", []):
            for fn in td.get("functionDeclarations", []):
                tools.append({"name": fn.get("name", ""), "description": fn.get("description", "")})

        return NormalizedRequest(
            provider=self.provider_name,
            model=self._cfg.get("model", ""),
            messages=messages,
            tools=tools,
            system_prompt=system_prompt,
            raw_body_dict=body,
            **nexus,
        )

    def extract_response_content(self, response_body: bytes) -> list[dict]:
        """Normalize Gemini candidates → Anthropic-style content blocks."""
        data = json.loads(response_body)
        blocks = []
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if text := part.get("text"):
                    blocks.append({"type": "text", "text": text})
                if fc := part.get("functionCall"):
                    blocks.append({
                        "type":  "tool_use",
                        "name":  fc.get("name", "unknown"),
                        "input": fc.get("args", {}),
                    })
        return blocks


# ── Ollama adapter (local models) ─────────────────────────────────────────────

class OllamaAdapter(ProviderAdapter):
    """
    Supports Ollama's OpenAI-compatible /api/chat endpoint and
    native /api/generate. Defaults to /api/chat (OpenAI-compat mode).
    Configure model in config.yaml providers.ollama.model.
    """

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def endpoint_url(self) -> str:
        host = self._cfg.get("host", "http://localhost:11434")
        path = self._cfg.get("path", "/api/chat")
        return f"{host}{path}"

    def build_headers(self) -> dict[str, str]:
        # Ollama local — no auth by default
        headers = {}
        if token := self._cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def normalize_request(self, headers: dict, body: dict) -> NormalizedRequest:
        nexus = self.extract_nexus_fields(headers)
        # Ollama /api/chat uses OpenAI-compatible message format
        system_prompt = ""
        messages = []
        for msg in body.get("messages", []):
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                messages.append(msg)

        return NormalizedRequest(
            provider=self.provider_name,
            model=body.get("model", self._cfg.get("model", "")),
            messages=messages,
            tools=body.get("tools", []),
            system_prompt=system_prompt,
            raw_body_dict=body,
            **nexus,
        )

    def extract_response_content(self, response_body: bytes) -> list[dict]:
        """Normalize Ollama /api/chat response → Anthropic-style blocks."""
        data = json.loads(response_body)
        blocks = []
        # /api/chat response
        if msg := data.get("message", {}):
            if text := msg.get("content"):
                blocks.append({"type": "text", "text": text})
            for tc in msg.get("tool_calls", []):
                fn = tc.get("function", {})
                blocks.append({
                    "type":  "tool_use",
                    "name":  fn.get("name", "unknown"),
                    "input": fn.get("arguments", {}),
                })
        # /api/generate response (fallback)
        elif text := data.get("response"):
            blocks.append({"type": "text", "text": text})
        return blocks


# ── OpenRouter adapter ────────────────────────────────────────────────────────

class OpenRouterAdapter(ProviderAdapter):
    """
    OpenRouter proxies 100+ models via a single OpenAI-compatible endpoint.
    Set providers.openrouter.model to any OpenRouter model string,
    e.g. "anthropic/claude-3-5-sonnet", "openai/gpt-4o", "meta-llama/llama-3.1-70b".
    """

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def endpoint_url(self) -> str:
        return self._cfg.get("endpoint", "https://openrouter.ai/api/v1/chat/completions")

    def build_headers(self) -> dict[str, str]:
        headers = {
            "Authorization":  f"Bearer {self._cfg.get('api_key', '')}",
            "HTTP-Referer":   self._cfg.get("site_url", "https://github.com/CyberStrategyInstitute/ai-safe2-framework"),
            "X-Title":        self._cfg.get("site_title", "AI SAFE² Gateway"),
        }
        return headers

    def normalize_request(self, headers: dict, body: dict) -> NormalizedRequest:
        nexus = self.extract_nexus_fields(headers)
        # OpenRouter uses OpenAI-compatible format
        system_prompt = ""
        messages = []
        for msg in body.get("messages", []):
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                messages.append(msg)

        tools = []
        for t in body.get("tools", []):
            if isinstance(t, dict):
                fn = t.get("function", t)
                tools.append({"name": fn.get("name", ""), "description": fn.get("description", "")})

        return NormalizedRequest(
            provider=self.provider_name,
            model=body.get("model", self._cfg.get("model", "")),
            messages=messages,
            tools=tools,
            system_prompt=system_prompt,
            raw_body_dict=body,
            **nexus,
        )

    def extract_response_content(self, response_body: bytes) -> list[dict]:
        """OpenRouter returns OpenAI-format responses."""
        data = json.loads(response_body)
        blocks = []
        for choice in data.get("choices", []):
            msg = choice.get("message", {})
            if text := msg.get("content"):
                blocks.append({"type": "text", "text": text})
            for tc in msg.get("tool_calls", []):
                fn = tc.get("function", {})
                try:
                    input_data = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    input_data = {"raw": fn.get("arguments", "")}
                blocks.append({
                    "type":  "tool_use",
                    "name":  fn.get("name", "unknown"),
                    "input": input_data,
                })
        return blocks


# ── Shared response scanner ───────────────────────────────────────────────────

EXFIL_PATTERNS = re.compile(
    r"(ANTHROPIC_API_KEY|sk-ant-|password|secret|credential|private.?key)",
    re.IGNORECASE,
)
RESPONSE_INJECTION_RE = re.compile(
    r"(ignore previous instructions|override safety|you are now|"
    r"new system prompt|ignore all prior)",
    re.IGNORECASE,
)


def _scan_normalized_blocks(blocks: list[dict]) -> tuple[bool, str]:
    """
    Scan normalized content blocks (Anthropic shape).
    Returns (is_clean, reason).
    """
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type", "")
        if block_type == "text":
            if EXFIL_PATTERNS.search(block.get("text", "")):
                return False, "Potential secret exfiltration in response text"
        elif block_type == "tool_use":
            tool_input_str = json.dumps(block.get("input", {}))
            if RESPONSE_INJECTION_RE.search(tool_input_str):
                return False, f"Injection payload in tool_use input for '{block.get('name', '?')}'"
            if EXFIL_PATTERNS.search(tool_input_str):
                return False, f"Potential secret exfiltration in tool_use input"
    return True, "clean"


# ── Registry / factory ────────────────────────────────────────────────────────

_ADAPTER_REGISTRY: dict[str, type[ProviderAdapter]] = {
    "anthropic":  AnthropicAdapter,
    "openai":     OpenAIAdapter,
    "gemini":     GeminiAdapter,
    "ollama":     OllamaAdapter,
    "openrouter": OpenRouterAdapter,
}


def get_adapter(provider: str, providers_config: dict) -> ProviderAdapter:
    """
    Return an initialized adapter for the named provider.

    Args:
        provider:         One of: anthropic, openai, gemini, ollama, openrouter
        providers_config: The full `providers:` section from config.yaml

    Raises:
        ValueError: If provider name is not recognized.
    """
    provider = provider.lower().strip()
    cls = _ADAPTER_REGISTRY.get(provider)
    if not cls:
        supported = ", ".join(_ADAPTER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider '{provider}'. Supported: {supported}"
        )
    provider_cfg = providers_config.get(provider, {})
    return cls(provider_cfg)


def list_providers() -> list[str]:
    """Return sorted list of supported provider names."""
    return sorted(_ADAPTER_REGISTRY.keys())


# ── NEXUS-A2A audit helper ────────────────────────────────────────────────────

def extract_nexus_audit_fields(normalized: NormalizedRequest) -> dict:
    """
    Return NEXUS fields from a NormalizedRequest for inclusion in the audit log.
    Returns empty dict if no NEXUS headers were present.
    This is the hook point for NEXUS runtime enforcement when it ships.
    """
    if not normalized.nexus_headers_present:
        return {}
    return {
        "nexus_agent_id":         normalized.nexus_agent_id,
        "nexus_session_id":       normalized.nexus_session_id,
        "nexus_delegation_chain": normalized.nexus_delegation_chain,
        "nexus_jurisdiction":     normalized.nexus_jurisdiction,
        "nexus_profile":          normalized.nexus_profile,
        "nexus_version":          normalized.nexus_version,
    }
