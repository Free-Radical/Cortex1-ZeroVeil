from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

Sink = Literal["jsonl", "stdout"]


@dataclass(frozen=True)
class AuditEvent:
    ts: int
    request_id: str
    tenant_id: str
    action: Literal["allow", "deny"]
    reason: str
    provider: str | None = None
    model: str | None = None
    message_count: int = 0
    total_chars: int = 0
    zdr_only: bool = True
    scrubbed_attested: bool = False
    latency_ms: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def now(**kwargs: Any) -> "AuditEvent":
        return AuditEvent(ts=int(time.time()), **kwargs)


class AuditLogger:
    def __init__(self, sink: Sink, path: str | None) -> None:
        self._sink = sink
        self._path = path

    def log(self, event: AuditEvent) -> None:
        data = asdict(event)
        line = json.dumps(data, ensure_ascii=False)
        if self._sink == "stdout":
            print(line)
            return
        if not self._path:
            return
        p = Path(self._path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
