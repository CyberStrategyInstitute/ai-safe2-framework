"""
AI SAFE² Gateway — Provider Adapters
Hermes Sovereign Runtime · Cyber Strategy Institute

Translates between Hermes/Anthropic-format requests and each upstream LLM provider.
Supports: Anthropic · OpenAI · Gemini · Ollama · OpenRouter · NIM · HuggingFace
"""

import os
from typing import Any


PROVIDER_ENDPOINTS = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com",
    "openrouter": "https://openrouter.ai/api",
    "gemini": "https://generativelanguage.googleapis.com",
    "ollama": "http://localhost:11434",
    "nim": "https://integrate.api.nvidia.com/v1",
    "huggingface": "https://api-inference.huggingface.co",
}

PATH_MAP = {
    "anthropic": {
        "/v1/messages": "/v1/messages",
        "/v1/chat/completions": "/v1/messages",
    },
    "openai": {
        "/v1/messages": "/v1/chat/completions",
        "/v1/chat/completions": "/v1/chat/completions",
    },
    "openrouter": {
        "/v1/messages": "/v1/chat/completions",
        "/v1/chat/completions": "/v1/chat/completions",
    },
    "ollama": {
        "/v1/messages": "/api/chat",
        "/v1/chat/completions": "/api/chat",
    },
}


def get_upstream_url(path: str, config: dict) -> str:
    provider = config.get("provider", {}).get("active", "anthropic")
    base = PROVIDER_ENDPOINTS.get(provider, PROVIDER_ENDPOINTS["anthropic"])

    # Check for custom base URL override (e.g., local Ollama, self-hosted)
    custom_base = config.get("provider", {}).get("base_url", "")
    if custom_base:
        base = custom_base.rstrip("/")

    mapped_path = PATH_MAP.get(provider, {}).get(path, path)
    return f"{base}{mapped_path}"


def translate_request(body: dict, provider: str) -> dict:
    """
    Translate Anthropic-format request body to provider-specific format if needed.
    Anthropic format is the canonical HSR format; translate outbound as needed.
    """
    if provider in ("anthropic",):
        return body  # Native format

    if provider in ("openai", "openrouter", "nim"):
        return _to_openai_format(body)

    if provider == "ollama":
        return _to_ollama_format(body)

    return body  # Pass through for unknown providers


def _to_openai_format(body: dict) -> dict:
    """Convert Anthropic messages format to OpenAI chat completions format."""
    translated = {
        "model": body.get("model", "gpt-4o"),
        "max_tokens": body.get("max_tokens", 4096),
        "stream": body.get("stream", False),
    }

    messages = []

    # Handle system prompt
    if "system" in body:
        system = body["system"]
        if isinstance(system, list):
            # Anthropic multi-block system
            system_text = " ".join(
                block.get("text", "") for block in system if block.get("type") == "text"
            )
        else:
            system_text = system
        messages.append({"role": "system", "content": system_text})

    # Convert messages
    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, list):
            # Multi-part content
            text_parts = [
                part.get("text", "") for part in content if part.get("type") == "text"
            ]
            content = " ".join(text_parts)
        messages.append({"role": role, "content": content})

    translated["messages"] = messages

    # Convert tools if present
    if "tools" in body:
        translated["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {}),
                },
            }
            for t in body["tools"]
        ]

    return translated


def _to_ollama_format(body: dict) -> dict:
    """Convert to Ollama's chat API format."""
    oai = _to_openai_format(body)
    return {
        "model": oai.get("model", "llama3"),
        "messages": oai.get("messages", []),
        "stream": oai.get("stream", False),
        "options": {
            "num_predict": oai.get("max_tokens", 4096),
        },
    }


def get_auth_headers(provider: str, config: dict) -> dict:
    """Return provider-specific authentication headers."""
    headers = {}

    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            headers["x-api-key"] = key
            headers["anthropic-version"] = "2023-06-01"

    elif provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "")
        if key:
            headers["Authorization"] = f"Bearer {key}"

    elif provider == "openrouter":
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        headers["HTTP-Referer"] = "https://cyberstrategyinstitute.com"
        headers["X-Title"] = "Hermes Sovereign Runtime"

    elif provider == "nim":
        key = os.environ.get("NIM_API_KEY", "")
        if key:
            headers["Authorization"] = f"Bearer {key}"

    elif provider == "huggingface":
        key = os.environ.get("HF_API_KEY", "")
        if key:
            headers["Authorization"] = f"Bearer {key}"

    # Ollama: no auth by default (local)

    return headers


def normalize_response(response_body: dict, provider: str) -> dict:
    """
    Normalize provider response to Anthropic messages format (canonical HSR format).
    Ensures consistent response structure regardless of upstream provider.
    """
    if provider == "anthropic":
        return response_body  # Already canonical

    if provider in ("openai", "openrouter", "nim"):
        return _from_openai_format(response_body)

    if provider == "ollama":
        return _from_ollama_format(response_body)

    return response_body


def _from_openai_format(body: dict) -> dict:
    """Convert OpenAI response to Anthropic messages format."""
    choices = body.get("choices", [])
    if not choices:
        return body

    choice = choices[0]
    message = choice.get("message", {})
    content = message.get("content", "")

    return {
        "id": body.get("id", ""),
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content}] if content else [],
        "model": body.get("model", ""),
        "stop_reason": choice.get("finish_reason", "end_turn"),
        "usage": {
            "input_tokens": body.get("usage", {}).get("prompt_tokens", 0),
            "output_tokens": body.get("usage", {}).get("completion_tokens", 0),
        },
    }


def _from_ollama_format(body: dict) -> dict:
    """Convert Ollama response to Anthropic messages format."""
    message = body.get("message", {})
    content = message.get("content", "")
    return {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content}],
        "model": body.get("model", ""),
        "stop_reason": "end_turn" if body.get("done") else "max_tokens",
    }
