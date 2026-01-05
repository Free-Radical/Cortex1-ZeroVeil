from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from zeroveil_gateway.pii import PIIDetectorConfig


class PolicyError(ValueError):
    pass


LoggingMode = Literal["metadata_only"]
LoggingSink = Literal["jsonl", "stdout"]

DEFAULT_MAX_SIZE_MB = 100
DEFAULT_MAX_AGE_DAYS = 30
DEFAULT_ROTATE_COUNT = 5


@dataclass(frozen=True)
class RetentionConfig:
    max_size_mb: int = DEFAULT_MAX_SIZE_MB
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    rotate_count: int = DEFAULT_ROTATE_COUNT


@dataclass(frozen=True)
class LogPath(os.PathLike[str]):
    path: str
    retention: RetentionConfig = field(default_factory=RetentionConfig)

    def __fspath__(self) -> str:
        return self.path

    def __str__(self) -> str:
        return self.path


@dataclass(frozen=True)
class Policy:
    version: str
    enforce_zdr_only: bool
    require_scrubbed_attestation: bool
    allowed_providers: list[str]
    allowed_models: list[str]
    max_messages: int
    max_chars_per_message: int
    logging_mode: LoggingMode
    logging_sink: LoggingSink
    logging_path: str | os.PathLike[str] | None
    logging_retention: RetentionConfig = field(default_factory=RetentionConfig)
    pii_gate: PIIDetectorConfig = field(default_factory=PIIDetectorConfig)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Policy":
        limits = data.get("limits") or {}
        logging_cfg = data.get("logging") or {}
        retention_cfg = logging_cfg.get("retention") or {}
        pii_gate_cfg = data.get("pii_gate")

        version = str(data.get("version", "0"))
        enforce_zdr_only = bool(data.get("enforce_zdr_only", True))
        require_scrubbed_attestation = bool(data.get("require_scrubbed_attestation", True))
        allowed_providers = list(data.get("allowed_providers") or [])
        allowed_models = list(data.get("allowed_models") or ["*"])

        max_messages = int(limits.get("max_messages", 50))
        max_chars_per_message = int(limits.get("max_chars_per_message", 16000))

        logging_mode = logging_cfg.get("mode", "metadata_only")
        if logging_mode != "metadata_only":
            raise PolicyError(f"Unsupported logging.mode: {logging_mode}")

        logging_sink = logging_cfg.get("sink", "jsonl")
        if logging_sink not in ("jsonl", "stdout"):
            raise PolicyError(f"Unsupported logging.sink: {logging_sink}")

        logging_path = logging_cfg.get("path")
        if logging_sink == "jsonl" and not logging_path:
            raise PolicyError("logging.path required when logging.sink is jsonl")

        retention = RetentionConfig(
            max_size_mb=int(retention_cfg.get("max_size_mb", DEFAULT_MAX_SIZE_MB)),
            max_age_days=int(retention_cfg.get("max_age_days", DEFAULT_MAX_AGE_DAYS)),
            rotate_count=int(retention_cfg.get("rotate_count", DEFAULT_ROTATE_COUNT)),
        )
        if retention.max_size_mb < 0:
            raise PolicyError("logging.retention.max_size_mb must be >= 0")
        if retention.max_age_days < 0:
            raise PolicyError("logging.retention.max_age_days must be >= 0")
        if retention.rotate_count < 0:
            raise PolicyError("logging.retention.rotate_count must be >= 0")

        if not allowed_providers:
            raise PolicyError("allowed_providers must be non-empty")

        return Policy(
            version=version,
            enforce_zdr_only=enforce_zdr_only,
            require_scrubbed_attestation=require_scrubbed_attestation,
            allowed_providers=allowed_providers,
            allowed_models=allowed_models,
            max_messages=max_messages,
            max_chars_per_message=max_chars_per_message,
            logging_mode=logging_mode,
            logging_sink=logging_sink,
            logging_path=LogPath(str(logging_path), retention=retention) if logging_path else None,
            logging_retention=retention,
            pii_gate=PIIDetectorConfig.from_dict(pii_gate_cfg),
        )

    @staticmethod
    def load(path: str | Path) -> "Policy":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise PolicyError("Policy file must be a JSON object")
        return Policy.from_dict(raw)
