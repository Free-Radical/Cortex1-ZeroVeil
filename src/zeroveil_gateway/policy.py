from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


class PolicyError(ValueError):
    pass


LoggingMode = Literal["metadata_only"]
LoggingSink = Literal["jsonl", "stdout"]


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
    logging_path: str | None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Policy":
        limits = data.get("limits") or {}
        logging_cfg = data.get("logging") or {}

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
            logging_path=str(logging_path) if logging_path else None,
        )

    @staticmethod
    def load(path: str | Path) -> "Policy":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise PolicyError("Policy file must be a JSON object")
        return Policy.from_dict(raw)

