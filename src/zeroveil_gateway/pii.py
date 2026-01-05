"""Minimal viable PII/PHI detector using regex patterns.

DESIGN PHILOSOPHY: FAIL-SAFE
============================
Security is OPT-OUT, not opt-in. This gate is ENABLED BY DEFAULT.
ZeroVeil errs on the side of rejecting potentially sensitive content.
False positives are acceptable; false negatives are not.

To disable (not recommended):
    "pii_gate": { "enabled": false }

WARNING: MINIMAL REGEX-BASED DETECTOR
======================================
This catches OBVIOUS patterns only. It is a TRIPWIRE, not comprehensive.

LIMITATIONS:
- NO name detection (won't catch "John Smith")
- NO address detection (won't catch "123 Main St")
- NO date of birth detection
- NO medical terms/PHI detection
- NO context awareness ("my SSN is NOT 123-45-6789" still triggers)
- Regex patterns may have false positives/negatives

WHAT IT CATCHES:
- SSN: 123-45-6789, 123 45 6789
- Credit cards: 1234-5678-9012-3456
- Email: user@example.com
- Phone: (123) 456-7890, 123-456-7890
- IP addresses: 192.168.1.1

For production use cases requiring higher accuracy, consider:
- Microsoft Presidio (Pro edition) - handles names, addresses, medical terms
- Custom NER models with context awareness
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

PII_TYPE = Literal["ssn", "email", "phone", "credit_card", "ip_address"]

# Compiled regex patterns for common PII types
PATTERNS: dict[PII_TYPE, re.Pattern[str]] = {
    # SSN: 123-45-6789 or 123 45 6789
    "ssn": re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"),
    # Email: user@domain.tld
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    # US Phone: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
    "phone": re.compile(r"(?:\(\d{3}\)\s?|\b\d{3}[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
    # Credit card: 16 digits with optional separators
    "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    # IPv4 address (potential identifier)
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

# Default enabled patterns (all patterns - gate is disabled by default anyway)
DEFAULT_ENABLED: frozenset[PII_TYPE] = frozenset({"ssn", "credit_card", "email", "phone", "ip_address"})


@dataclass(frozen=True)
class PIIMatch:
    """A detected PII match."""

    pii_type: PII_TYPE
    start: int
    end: int
    # Note: We do NOT store the matched text to avoid logging PII


@dataclass(frozen=True)
class PIIDetectorConfig:
    """Configuration for PII detection.

    FAIL-SAFE DESIGN: Enabled by default. Security is opt-OUT, not opt-in.
    """

    enabled: bool = True
    patterns: frozenset[PII_TYPE] = DEFAULT_ENABLED

    @staticmethod
    def from_dict(data: dict[str, object] | None) -> PIIDetectorConfig:
        if data is None:
            return PIIDetectorConfig()

        enabled = bool(data.get("enabled", True))  # FAIL-SAFE: enabled by default
        patterns_raw = data.get("patterns")

        if patterns_raw is None:
            patterns = DEFAULT_ENABLED
        elif isinstance(patterns_raw, list):
            valid_patterns: set[PII_TYPE] = set()
            for p in patterns_raw:
                if p in PATTERNS:
                    valid_patterns.add(p)  # type: ignore[arg-type]
            patterns = frozenset(valid_patterns) if valid_patterns else DEFAULT_ENABLED
        else:
            patterns = DEFAULT_ENABLED

        return PIIDetectorConfig(enabled=enabled, patterns=patterns)


class PIIDetector:
    """Regex-based PII detector.

    This is a minimal viable detector for the Community edition.
    It provides reject-only functionality - detects PII and returns matches,
    but never scrubs or modifies content.
    """

    def __init__(self, config: PIIDetectorConfig) -> None:
        self.config = config
        self._active_patterns: dict[PII_TYPE, re.Pattern[str]] = {
            pii_type: pattern
            for pii_type, pattern in PATTERNS.items()
            if pii_type in config.patterns
        }

    def scan(self, text: str) -> list[PIIMatch]:
        """Scan text for PII patterns.

        Returns a list of PIIMatch objects (without the matched text).
        Returns empty list if detector is disabled.
        """
        if not self.config.enabled:
            return []

        matches: list[PIIMatch] = []
        for pii_type, pattern in self._active_patterns.items():
            for match in pattern.finditer(text):
                matches.append(
                    PIIMatch(pii_type=pii_type, start=match.start(), end=match.end())
                )

        return matches

    def contains_pii(self, text: str) -> bool:
        """Quick check if text contains any PII.

        More efficient than scan() when you only need a boolean result.
        """
        if not self.config.enabled:
            return False

        for pattern in self._active_patterns.values():
            if pattern.search(text):
                return True

        return False

    def scan_messages(self, messages: list[dict[str, str | None]]) -> dict[int, list[PIIMatch]]:
        """Scan a list of messages for PII.

        Args:
            messages: List of message dicts with 'content' key

        Returns:
            Dict mapping message index to list of PIIMatch objects.
            Only includes indices with matches.
        """
        if not self.config.enabled:
            return {}

        results: dict[int, list[PIIMatch]] = {}
        for i, msg in enumerate(messages):
            content = msg.get("content") or ""
            if isinstance(content, str):
                matches = self.scan(content)
                if matches:
                    results[i] = matches

        return results