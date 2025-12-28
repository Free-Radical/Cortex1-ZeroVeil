from __future__ import annotations

import json
import os

import requests


def main() -> int:
    base = os.getenv("ZEROVEIL_ENDPOINT", "http://localhost:8000")
    api_key = os.getenv("ZEROVEIL_API_KEY", "")

    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "zdr_only": True,
        "metadata": {"scrubbed": True, "scrubber": "demo", "scrubber_version": "0"},
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resp = requests.post(f"{base}/v1/chat/completions", headers=headers, json=payload, timeout=30)
    print(resp.status_code)
    print(json.dumps(resp.json(), indent=2))
    return 0 if resp.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
