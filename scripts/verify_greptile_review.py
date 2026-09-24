#!/usr/bin/env python3
"""Report whether Greptile completed a substantive review of the current PR head."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any


GREPTILE_LOGINS = {"greptile-apps", "greptile-apps[bot]"}
DEGRADED_MARKERS = (
    "credit limit",
    "trial limit",
    "upgrade your plan",
    "quota",
    "rate limit",
    "unable to review",
    "review failed",
    "could not review",
    "did not run",
)


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reason: str


def _login(item: dict[str, Any]) -> str:
    return str((item.get("user") or {}).get("login") or "").lower()


def _body(item: dict[str, Any]) -> str:
    return str(item.get("body") or "").strip()


def evaluate(
    *,
    head_sha: str,
    reviews: list[dict[str, Any]],
    issue_comments: list[dict[str, Any]],
    review_comments: list[dict[str, Any]],
) -> GateResult:
    """Evaluate API payloads without trusting a mere bot appearance as approval."""
    bot_reviews = [
        review
        for review in reviews
        if _login(review) in GREPTILE_LOGINS and review.get("commit_id") == head_sha
    ]
    if not bot_reviews:
        return GateResult(False, f"Greptile has not reviewed current head {head_sha[:12]}.")

    bot_reviews.sort(key=lambda item: str(item.get("submitted_at") or ""), reverse=True)
    latest = bot_reviews[0]
    review_id = latest.get("id")
    linked_inline = [
        comment
        for comment in review_comments
        if _login(comment) in GREPTILE_LOGINS
        and (
            comment.get("pull_request_review_id") == review_id
            or comment.get("commit_id") == head_sha
        )
    ]
    submitted_at = str(latest.get("submitted_at") or "")
    bot_issue_comments = [
        comment
        for comment in issue_comments
        if _login(comment) in GREPTILE_LOGINS
        and str(comment.get("updated_at") or comment.get("created_at") or "") >= submitted_at
    ]
    evidence_text = "\n".join(
        [_body(latest)]
        + [_body(comment) for comment in linked_inline]
        + [_body(comment) for comment in bot_issue_comments]
    ).lower()

    degraded = next((marker for marker in DEGRADED_MARKERS if marker in evidence_text), None)
    if degraded:
        return GateResult(
            False,
            f"Greptile responded for {head_sha[:12]} but did not complete a review "
            f"(detected: {degraded!r}).",
        )

    substantive = bool(linked_inline) or len(_body(latest)) >= 80
    if not substantive:
        substantive = any(len(_body(comment)) >= 120 for comment in bot_issue_comments)
    if not substantive:
        return GateResult(
            False,
            "Greptile touched the current head, but no substantive review output was found.",
        )

    submitted = latest.get("submitted_at") or "unknown time"
    return GateResult(
        True,
        f"Greptile completed a review of {head_sha[:12]} at {submitted}; "
        f"{len(linked_inline)} inline finding(s) observed.",
    )


class GitHubClient:
    def __init__(self, *, repository: str, token: str) -> None:
        self.repository = repository
        self.token = token

    def get_all(self, endpoint: str) -> list[dict[str, Any]]:
        url = f"https://api.github.com/repos/{self.repository}/{endpoint}"
        items: list[dict[str, Any]] = []
        while url:
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.token}",
                    "User-Agent": "greptile-current-head-gate",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
                if not isinstance(payload, list):
                    raise RuntimeError(f"Expected a list from {endpoint}")
                items.extend(payload)
                url = _next_link(response.headers.get("Link", ""))
        return items


def _next_link(link_header: str) -> str:
    for part in link_header.split(","):
        sections = [section.strip() for section in part.split(";")]
        if len(sections) == 2 and sections[1] == 'rel="next"':
            return sections[0].strip("<>")
    return ""


def _write_summary(result: GateResult, *, advisory: bool = False) -> None:
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    marker = "PASS" if result.ok else ("NOTICE" if advisory else "FAIL")
    with open(summary, "a", encoding="utf-8") as handle:
        handle.write(f"## Greptile current-head gate: {marker}\n\n{result.reason}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY"))
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=720)
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument(
        "--advisory",
        action="store_true",
        help="Report missing/degraded review without failing the workflow.",
    )
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN", "")
    if not args.repository or not token:
        print("GITHUB_REPOSITORY and GITHUB_TOKEN are required.", file=sys.stderr)
        return 2

    client = GitHubClient(repository=args.repository, token=token)
    deadline = time.monotonic() + args.timeout_seconds
    last_result = GateResult(False, "Greptile evidence has not been checked yet.")

    while True:
        try:
            last_result = evaluate(
                head_sha=args.head_sha,
                reviews=client.get_all(f"pulls/{args.pr}/reviews?per_page=100"),
                issue_comments=client.get_all(f"issues/{args.pr}/comments?per_page=100"),
                review_comments=client.get_all(f"pulls/{args.pr}/comments?per_page=100"),
            )
        except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
            last_result = GateResult(False, f"Could not read Greptile evidence: {exc}")

        print(f"[{datetime.now().isoformat(timespec='seconds')}] {last_result.reason}")
        if last_result.ok:
            _write_summary(last_result, advisory=args.advisory)
            return 0
        if time.monotonic() >= deadline:
            _write_summary(last_result, advisory=args.advisory)
            if args.advisory:
                print("Greptile did not complete a substantive current-head review; continuing.")
                return 0
            print(
                "Greptile is a required final review gate. Check installation, repository access, "
                "quota/plan status, and whether it reviewed the latest commit.",
                file=sys.stderr,
            )
            return 1
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
