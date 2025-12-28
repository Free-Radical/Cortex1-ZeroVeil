from __future__ import annotations

import json
from pathlib import Path

from zeroveil_gateway.audit import AuditEvent, AuditLogger


def test_auditlogger_jsonl_writes_one_json_per_line(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    audit = AuditLogger(sink="jsonl", path=str(log_path))

    audit.log(
        AuditEvent.now(
            request_id="zv_test",
            tenant_id="t1",
            action="allow",
            reason="ok",
            provider="stub",
            model="stub",
            message_count=1,
            total_chars=5,
            zdr_only=True,
            scrubbed_attested=True,
            latency_ms=1,
            extra={"k": "v"},
        )
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["request_id"] == "zv_test"
    assert data["action"] == "allow"

