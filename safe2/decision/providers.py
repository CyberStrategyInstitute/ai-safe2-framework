"""Provider abstraction for TypeSafe-compatible System One endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class DecisionProvider(Protocol):
    name: str
    model: str

    def decide(self, state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class SystemOneProvider:
    name: str
    endpoint: str
    model: str
    api_key: str | None = None
    timeout_seconds: float = 8.0

    def decide(self, state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
        headers = {"authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
            response = client.post(
                self.endpoint.rstrip("/") + "/v1/systemone",
                headers=headers,
                json={"model": self.model, "state": state, "questions": questions},
            )
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict) or not isinstance(value.get("answers"), dict):
            raise TypeError("provider returned an invalid System One response")
        return value
