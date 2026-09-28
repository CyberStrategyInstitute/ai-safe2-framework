"""Provider abstraction for TypeSafe-compatible System One endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlsplit

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
    require_https: bool = False

    def __post_init__(self) -> None:
        parsed = urlsplit(self.endpoint)
        allowed = {"https"} if self.require_https else {"http", "https"}
        if parsed.scheme not in allowed or not parsed.hostname:
            expected = "HTTPS" if self.require_https else "HTTP(S)"
            raise ValueError(f"provider endpoint must be an absolute {expected} URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("provider endpoint must not contain credentials, query, or fragment")

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
        if set(value["answers"]) != set(questions):
            raise TypeError("provider response does not match the requested question set")
        for answer in value["answers"].values():
            if not isinstance(answer, dict):
                raise TypeError("provider answer must be an object")
            for probability in ("confidence", "noul"):
                if probability in answer and (
                    isinstance(answer[probability], bool)
                    or not isinstance(answer[probability], (int, float))
                    or not 0 <= float(answer[probability]) <= 1
                ):
                    raise TypeError(f"provider {probability} must be between 0 and 1")
        return value
