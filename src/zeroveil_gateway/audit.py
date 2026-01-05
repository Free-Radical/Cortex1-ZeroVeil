from __future__ import annotations

import glob
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from zeroveil_gateway.policy import RetentionConfig

Sink = Literal["jsonl", "stdout"]


@dataclass(frozen=True)
class AuditEvent:
    ts: int
    request_id: str
    tenant_id: str
    action: Literal["allow", "deny"]
    reason: str
    schema_version: str = "1"
    ts_iso: str = ""
    client_ip: str | None = None
    user_agent: str | None = None
    provider: str | None = None
    model: str | None = None
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    message_count: int = 0
    total_chars: int = 0
    zdr_only: bool = True
    scrubbed_attested: bool = False
    latency_ms: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ts_iso:
            object.__setattr__(
                self,
                "ts_iso",
                datetime.fromtimestamp(self.ts, tz=timezone.utc).isoformat(),
            )

    @staticmethod
    def now(**kwargs: Any) -> "AuditEvent":
        return AuditEvent(ts=int(time.time()), **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ts": self.ts,
            "ts_iso": self.ts_iso,
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "action": self.action,
            "reason": self.reason,
            "provider": self.provider,
            "model": self.model,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "message_count": self.message_count,
            "total_chars": self.total_chars,
            "zdr_only": self.zdr_only,
            "scrubbed_attested": self.scrubbed_attested,
            "latency_ms": self.latency_ms,
            "extra": self.extra,
        }


class AuditLogger:
    def __init__(self, sink: Sink, path: str | os.PathLike[str] | None, *, retention: RetentionConfig | None = None) -> None:
        self._sink = sink
        self._path = path
        self._retention = retention or getattr(path, "retention", RetentionConfig())

    def log(self, event: AuditEvent) -> None:
        data = event.to_dict()
        line = json.dumps(data, ensure_ascii=False)
        if self._sink == "stdout":
            print(line)
            return
        if not self._path:
            return
        p = Path(self._path)
        p.parent.mkdir(parents=True, exist_ok=True)

        self._maybe_rotate(p)

        with p.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _maybe_rotate(self, path: Path) -> None:
        cfg = self._retention
        if cfg.rotate_count <= 0 or cfg.max_size_mb <= 0:
            return

        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return

        max_bytes = cfg.max_size_mb * 1024 * 1024
        if size < max_bytes:
            return

        # Shift existing rotations: audit.jsonl.(n-1) -> audit.jsonl.n
        for i in range(cfg.rotate_count - 1, 0, -1):
            src = Path(f"{path}.{i}")
            dst = Path(f"{path}.{i + 1}")
            if src.exists():
                os.replace(src, dst)

        # Move current log to .1 last to avoid losing it on crash mid-rotation.
        os.replace(path, Path(f"{path}.1"))

        self._cleanup_rotated_files(path)

    def _cleanup_rotated_files(self, base_path: Path) -> None:
        cfg = self._retention
        if cfg.rotate_count <= 0:
            return

        cutoff = time.time() - (cfg.max_age_days * 86400)
        prefix = f"{base_path}."

        for path_str in glob.glob(f"{base_path}.*"):
            if not path_str.startswith(prefix):
                continue
            suffix = path_str[len(prefix) :]
            try:
                idx = int(suffix)
            except ValueError:
                continue

            p = Path(path_str)
            if idx > cfg.rotate_count:
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass
                continue

            if cfg.max_age_days <= 0:
                continue

            try:
                mtime = p.stat().st_mtime
            except FileNotFoundError:
                continue

            if mtime < cutoff:
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass
