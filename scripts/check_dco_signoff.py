from __future__ import annotations

import json
import os
from typing import Any

import requests


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _has_signoff(message: str) -> bool:
    lower = message.lower()
    return "signed-off-by:" in lower


def main() -> int:
    repo = _get_required_env("GITHUB_REPOSITORY")
    token = _get_required_env("GITHUB_TOKEN")
    event_path = _get_required_env("GITHUB_EVENT_PATH")

    event: dict[str, Any] = json.loads(open(event_path, "r", encoding="utf-8").read())

    pr = event.get("pull_request")
    if not pr:
        print("No pull_request in event; skipping DCO check.")
        return 0

    pr_number = pr.get("number")
    if not pr_number:
        print("No PR number; skipping DCO check.")
        return 0

    api = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/commits"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    commits = requests.get(api, headers=headers, timeout=30).json()
    if not isinstance(commits, list):
        raise RuntimeError(f"Unexpected response from GitHub API: {commits}")

    bad = []
    for c in commits:
        sha = c.get("sha")
        commit = (c.get("commit") or {})
        message = commit.get("message") or ""
        if not _has_signoff(message):
            bad.append(sha)

    if bad:
        print("DCO check failed: the following commits are missing Signed-off-by lines:")
        for sha in bad:
            print(f"- {sha}")
        print("\nFix by re-committing with: git commit -s --amend (or rebase and sign each commit).")
        return 1

    print("DCO check passed: all PR commits contain Signed-off-by.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
