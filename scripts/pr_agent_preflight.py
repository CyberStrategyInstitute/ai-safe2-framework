#!/usr/bin/env python3
"""Select an available free OpenRouter model with a bounded review canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

CANARY = """\
def download_report(user, report_id, root):
    report = db.get_report(report_id)                         # C1
    data = (root / report.filename).read_bytes()             # C2
    if report.owner_id != user.id:                           # C3
        raise PermissionError
    return data                                               # C4

def download_avatar(user, root):
    trusted_root = root.resolve()                             # S1
    candidate = (trusted_root / f"{user.id}.png").resolve() # S2
    if trusted_root not in candidate.parents:                # S3
        raise ValueError("unsafe path")
    return candidate.read_bytes()                             # S4
"""


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_json(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    try:
        value = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def _is_zero_price(value: Any) -> bool:
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _not_expired(value: Any, now: datetime) -> bool:
    if value in (None, ""):
        return True
    try:
        if isinstance(value, (int, float)):
            expires = datetime.fromtimestamp(value, tz=UTC)
        else:
            text = str(value)
            if text.endswith("Z"):
                text = f"{text[:-1]}+00:00"
            expires = datetime.fromisoformat(text)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
    except (OSError, OverflowError, ValueError):
        return False
    return expires > now


def _is_eligible_free_text_model(
    model: dict[str, Any],
    minimum_context_tokens: int,
    now: datetime,
) -> bool:
    pricing = model.get("pricing", {})
    return bool(
        _is_zero_price(pricing.get("prompt"))
        and _is_zero_price(pricing.get("completion"))
        and _is_zero_price(pricing.get("request", 0))
        and "text" in model.get("architecture", {}).get("output_modalities", [])
        and int(model.get("context_length") or 0) >= minimum_context_tokens
        and _not_expired(model.get("expiration_date"), now)
    )


def eligible_candidates(
    catalog: dict[str, Any],
    configured: list[str],
    minimum_context_tokens: int = 0,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], int]:
    observed_at = now or datetime.now(tz=UTC)
    models = {
        item.get("id"): item
        for item in catalog.get("data", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    eligible_total = sum(
        1
        for model in models.values()
        if _is_eligible_free_text_model(model, minimum_context_tokens, observed_at)
    )
    retained: list[dict[str, Any]] = []
    for model_id in configured:
        model = models.get(model_id, {})
        if _is_eligible_free_text_model(model, minimum_context_tokens, observed_at):
            retained.append(model)
    return retained, eligible_total


def endpoint_health(model: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    endpoints = payload.get("data", {}).get("endpoints", [])
    free_endpoints = [
        endpoint
        for endpoint in endpoints
        if isinstance(endpoint, dict)
        and _is_zero_price(endpoint.get("pricing", {}).get("prompt"))
        and _is_zero_price(endpoint.get("pricing", {}).get("completion"))
    ]

    def recent_uptime(endpoint: dict[str, Any]) -> float:
        for field in ("uptime_last_5m", "uptime_last_30m", "uptime_last_1d"):
            value = endpoint.get(field)
            if isinstance(value, (int, float)):
                return float(value)
        return -1.0

    best = max(free_endpoints, key=recent_uptime) if free_endpoints else None
    return {
        "model": model["id"],
        "expiration_date": model.get("expiration_date"),
        "online": best is not None and best.get("status") == 0,
        "provider": best.get("provider_name") if best else None,
        "status": best.get("status") if best else None,
        "uptime_last_5m": best.get("uptime_last_5m") if best else None,
        "uptime_last_30m": best.get("uptime_last_30m") if best else None,
        "uptime_last_1d": best.get("uptime_last_1d") if best else None,
        "recent_uptime": recent_uptime(best) if best else -1.0,
    }


def model_details_url(model: dict[str, Any]) -> str:
    model_id = str(model["id"])
    details_path = model.get("links", {}).get("details")
    # Catalog links for :free variants may resolve to the canonical paid model.
    # Preserve the exact variant so health and zero-price evidence describe the
    # route that will actually receive the review.
    if model_id.endswith(":free") or not details_path:
        author, slug = model_id.split("/", 1)
        details_path = (
            "/api/v1/models/"
            f"{urllib.parse.quote(author, safe='')}/"
            f"{urllib.parse.quote(slug, safe=':')}/endpoints"
        )
    return urllib.parse.urljoin("https://openrouter.ai", str(details_path))


def shortlist_by_health(
    health: list[dict[str, Any]],
    *,
    size: int,
    minimum_recent_uptime: float,
) -> list[str]:
    qualified = [
        record
        for record in health
        if float(record.get("recent_uptime", -1)) >= minimum_recent_uptime
    ]
    qualified.sort(
        key=lambda record: (
            -float(record.get("recent_uptime", -1)),
            -float(record.get("uptime_last_30m") or -1),
            -float(record.get("uptime_last_1d") or -1),
            str(record["model"]),
        )
    )
    return [str(record["model"]) for record in qualified[:size]]


def select_pr_patch(files: list[dict[str, Any]], policy: dict[str, Any]) -> tuple[str, str]:
    limit = int(policy["pr_context"]["maximum_patch_characters"])
    priorities = [value.lower() for value in policy["pr_context"]["priority_path_fragments"]]
    usable = [item for item in files if item.get("patch") and item.get("filename")]
    if not usable:
        return "unavailable", "No textual patch was available for the compatibility probe."

    def rank(item: dict[str, Any]) -> tuple[int, str]:
        filename = str(item["filename"]).lower()
        matches = [index for index, fragment in enumerate(priorities) if fragment in filename]
        return (min(matches) if matches else len(priorities), filename)

    chosen = min(usable, key=rank)
    filename = str(chosen["filename"])
    patch = str(chosen["patch"])[:limit]
    return filename, patch


def build_prompt(pr_path: str, pr_patch: str, maximum_findings: int) -> str:
    return f"""\
You are running a compact code-review compatibility benchmark. Return JSON only.

For CANARY, report exactly the real security defects and do not flag verified-safe lines.
Allowed defect_id values are "authorization-after-read" and "path-traversal".
For PR_CONTEXT, provide at most one concise potential issue, or null when evidence is insufficient.
Do not invent missing context. Keep the entire response under 2200 characters.

Required shape:
{{"canary_findings":[{{"defect_id":"...","line_id":"C#","why":"..."}}],
 "safe_line_findings":[],
 "pr_context":{{"path":"{pr_path}","potential_issue":null,"why":"..."}}}}

CANARY:
```python
{CANARY}```

PR_CONTEXT ({pr_path}):
```diff
{pr_patch}
```

The canary must contain no more than {maximum_findings} findings.
"""


def assess_response(text: str, policy: dict[str, Any]) -> dict[str, Any]:
    parsed = _extract_json(text)
    result: dict[str, Any] = {
        "valid_json": parsed is not None,
        "required_defects_found": [],
        "safe_false_positives": [],
        "finding_count": 0,
        "response_characters": len(text),
        "concise": len(text) <= int(policy["selection"]["maximum_response_characters"]),
        "passed": False,
        "score": 0,
    }
    if parsed is None:
        return result
    findings = parsed.get("canary_findings")
    safe_findings = parsed.get("safe_line_findings")
    if not isinstance(findings, list) or not isinstance(safe_findings, list):
        return result
    required = policy["selection"]["required_defects"]
    observed = {
        str(item.get("defect_id")): str(item.get("line_id"))
        for item in findings
        if isinstance(item, dict) and item.get("defect_id") in required
    }
    safe_ids = set(policy["selection"]["safe_line_ids"])
    false_positives = [
        item
        for item in safe_findings
        if isinstance(item, dict) and str(item.get("line_id")) in safe_ids
    ]
    result.update(
        {
            "required_defects_found": sorted(observed),
            "safe_false_positives": false_positives,
            "finding_count": len(findings),
        }
    )
    correct = observed == required
    bounded = len(findings) <= int(policy["selection"]["maximum_findings"])
    result["passed"] = bool(correct and not false_positives and bounded and result["concise"])
    result["score"] = (
        30 * sum(observed.get(defect_id) == line_id for defect_id, line_id in required.items())
        + (20 if not false_positives else 0)
        + (10 if result["valid_json"] and bounded else 0)
        + (10 if len(text) <= 1200 else 5 if result["concise"] else 0)
    )
    return result


def _error_details(error: Exception) -> tuple[str, int | None]:
    if isinstance(error, urllib.error.HTTPError):
        try:
            payload = json.loads(error.read().decode("utf-8"))
            message = payload.get("error", {}).get("message") or str(error)
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = str(error)
        return str(message)[:500], error.code
    return f"{type(error).__name__}: {error}"[:500], None


def probe_model(
    model: str,
    prompt: str,
    api_key: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    request_policy = policy["request"]
    started = time.perf_counter()
    record: dict[str, Any] = {
        "model": model,
        "available": False,
        "latency_ms": None,
        "http_status": None,
        "error": None,
        "response_sha256": None,
        "assessment": None,
    }
    try:
        response = _request_json(
            OPENROUTER_CHAT_URL,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/CyberStrategyInstitute/ai-safe2-framework",
                "X-Title": "AI SAFE2 PR-Agent preflight",
            },
            payload={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": request_policy["temperature"],
                "max_tokens": request_policy["max_completion_tokens"],
            },
            timeout=int(request_policy["timeout_seconds"]),
        )
        record["http_status"] = 200
        content = response["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty model response")
        assessment = assess_response(content, policy)
        record.update(
            {
                "available": True,
                "http_status": 200,
                "response_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "assessment": assessment,
            }
        )
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ) as error:  # Network and provider failures are evidence, not crashes.
        message, status = _error_details(error)
        record.update({"error": message, "http_status": status})
    record["latency_ms"] = round((time.perf_counter() - started) * 1000)
    return record


def write_outputs(path: str | None, values: dict[str, str]) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.writelines(f"{key}={value}\n" for key, value in values.items())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = os.environ.get("PR_NUMBER", "")
    candidate_pool = list(policy["candidate_pool"])
    discovery = policy["discovery"]
    receipt: dict[str, Any] = {
        "schema_version": "safe2.pr-agent-preflight.v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repository": repository,
        "pr_number": int(pr_number) if pr_number.isdigit() else None,
        "benchmark_version": policy["benchmark_version"],
        "candidate_pool": candidate_pool,
        "eligible_free_models_in_catalog": None,
        "catalog_candidates": [],
        "endpoint_health": [],
        "shortlisted_candidates": [],
        "tested_candidates": [],
        "selected_model": None,
        "status": "unavailable",
    }
    if not api_key:
        receipt["failure_reason"] = "OPENROUTER_API_KEY is not configured"
    else:
        try:
            catalog = _request_json(
                OPENROUTER_MODELS_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=int(policy["request"]["timeout_seconds"]),
            )
            candidate_models, eligible_total = eligible_candidates(
                catalog,
                candidate_pool,
                int(discovery["minimum_context_tokens"]),
            )
            receipt["eligible_free_models_in_catalog"] = eligible_total
            receipt["catalog_candidates"] = [model["id"] for model in candidate_models]
            for model in candidate_models:
                details_url = model_details_url(model)
                try:
                    endpoint_payload = _request_json(
                        details_url,
                        headers={"Authorization": f"Bearer {api_key}"},
                        timeout=int(policy["request"]["timeout_seconds"]),
                    )
                    receipt["endpoint_health"].append(endpoint_health(model, endpoint_payload))
                except (
                    urllib.error.URLError,
                    TimeoutError,
                    OSError,
                    KeyError,
                    IndexError,
                    TypeError,
                    ValueError,
                ) as error:
                    message, status = _error_details(error)
                    receipt["endpoint_health"].append(
                        {
                            "model": model["id"],
                            "online": False,
                            "recent_uptime": -1,
                            "metadata_error": message,
                            "metadata_http_status": status,
                        }
                    )
            candidates = shortlist_by_health(
                receipt["endpoint_health"],
                size=int(discovery["shortlist_size"]),
                minimum_recent_uptime=float(discovery["minimum_recent_uptime_percent"]),
            )
            receipt["shortlisted_candidates"] = candidates
            files: list[dict[str, Any]] = []
            if github_token and repository and pr_number.isdigit():
                files_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/files?per_page=100"
                files_payload = _request_json(
                    files_url,
                    headers={
                        "Authorization": f"Bearer {github_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                    timeout=20,
                )
                if isinstance(files_payload, list):
                    files = files_payload
            pr_path, pr_patch = select_pr_patch(files, policy)
            prompt = build_prompt(
                pr_path,
                pr_patch,
                int(policy["selection"]["maximum_findings"]),
            )
            receipt["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            receipt["pr_context"] = {
                "path": pr_path,
                "patch_sha256": hashlib.sha256(pr_patch.encode("utf-8")).hexdigest(),
                "patch_characters": len(pr_patch),
            }
            for model in candidates:
                receipt["tested_candidates"].append(probe_model(model, prompt, api_key, policy))
            passing = [
                item
                for item in receipt["tested_candidates"]
                if item.get("available") and item.get("assessment", {}).get("passed")
            ]
            if passing:
                passing.sort(
                    key=lambda item: (
                        -int(item["assessment"]["score"]),
                        int(item["assessment"]["response_characters"]),
                        int(item["latency_ms"]),
                        str(item["model"]),
                    )
                )
                receipt["selected_model"] = passing[0]["model"]
                receipt["status"] = "selected"
            elif not candidates:
                receipt["failure_reason"] = (
                    "no candidate passed live catalog, expiry, status, and uptime filters"
                )
            else:
                receipt["failure_reason"] = "no tested candidate passed the review canary"
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as error:
            receipt["failure_reason"], receipt["catalog_http_status"] = _error_details(error)

    encoded = f"{json.dumps(receipt, indent=2, sort_keys=True)}\n"
    args.receipt.write_text(encoded, encoding="utf-8")
    selected = receipt["selected_model"] or ""
    write_outputs(
        os.environ.get("GITHUB_OUTPUT"),
        {
            "available": str(bool(selected)).lower(),
            "selected_model": selected,
            "tested_count": str(len(receipt["tested_candidates"])),
            "eligible_count": str(receipt["eligible_free_models_in_catalog"] or 0),
            "receipt_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        },
    )
    print(
        f"Preflight {receipt['status']}: tested {len(receipt['tested_candidates'])} of "
        f"{receipt['eligible_free_models_in_catalog'] or 0} eligible free models; "
        f"selected {selected or 'none'}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
