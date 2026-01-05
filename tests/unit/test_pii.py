"""Unit tests for PII detector module."""

from __future__ import annotations

import pytest

from zeroveil_gateway.pii import (
    DEFAULT_ENABLED,
    PIIDetector,
    PIIDetectorConfig,
    PIIMatch,
)


class TestPIIDetectorConfig:
    def test_default_config_enabled_by_default(self) -> None:
        """FAIL-SAFE: PII gate is ENABLED by default."""
        config = PIIDetectorConfig()
        assert config.enabled is True  # Security is opt-OUT
        assert config.patterns == DEFAULT_ENABLED

    def test_from_dict_none_enabled_by_default(self) -> None:
        """FAIL-SAFE: Missing config means enabled."""
        config = PIIDetectorConfig.from_dict(None)
        assert config.enabled is True  # Security is opt-OUT
        assert config.patterns == DEFAULT_ENABLED

    def test_from_dict_empty_enabled_by_default(self) -> None:
        """FAIL-SAFE: Empty config means enabled."""
        config = PIIDetectorConfig.from_dict({})
        assert config.enabled is True  # Security is opt-OUT
        assert config.patterns == DEFAULT_ENABLED

    def test_from_dict_explicit_disable(self) -> None:
        """User must explicitly opt-OUT of security."""
        config = PIIDetectorConfig.from_dict({"enabled": False})
        assert config.enabled is False
        assert config.patterns == DEFAULT_ENABLED

    def test_from_dict_custom_patterns(self) -> None:
        config = PIIDetectorConfig.from_dict({
            "enabled": True,
            "patterns": ["ssn", "email", "phone"]
        })
        assert config.enabled is True
        assert config.patterns == frozenset({"ssn", "email", "phone"})

    def test_from_dict_invalid_patterns_ignored(self) -> None:
        config = PIIDetectorConfig.from_dict({
            "enabled": True,
            "patterns": ["ssn", "invalid_type", "credit_card"]
        })
        assert config.patterns == frozenset({"ssn", "credit_card"})

    def test_from_dict_all_invalid_patterns_uses_default(self) -> None:
        config = PIIDetectorConfig.from_dict({
            "enabled": True,
            "patterns": ["invalid1", "invalid2"]
        })
        assert config.patterns == DEFAULT_ENABLED

    def test_from_dict_patterns_not_list_uses_default(self) -> None:
        config = PIIDetectorConfig.from_dict({
            "enabled": True,
            "patterns": "ssn"  # Wrong type
        })
        assert config.patterns == DEFAULT_ENABLED


class TestPIIDetector:
    def test_disabled_detector_returns_empty(self) -> None:
        config = PIIDetectorConfig(enabled=False)
        detector = PIIDetector(config)
        text = "My SSN is 123-45-6789"
        assert detector.scan(text) == []
        assert detector.contains_pii(text) is False

    def test_detect_ssn_dashes(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn"}))
        detector = PIIDetector(config)
        matches = detector.scan("My SSN is 123-45-6789")
        assert len(matches) == 1
        assert matches[0].pii_type == "ssn"

    def test_detect_ssn_spaces(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn"}))
        detector = PIIDetector(config)
        matches = detector.scan("SSN: 123 45 6789")
        assert len(matches) == 1
        assert matches[0].pii_type == "ssn"

    def test_detect_credit_card(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"credit_card"}))
        detector = PIIDetector(config)
        # With dashes
        matches = detector.scan("Card: 1234-5678-9012-3456")
        assert len(matches) == 1
        assert matches[0].pii_type == "credit_card"

    def test_detect_credit_card_no_separator(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"credit_card"}))
        detector = PIIDetector(config)
        matches = detector.scan("Card: 1234567890123456")
        assert len(matches) == 1
        assert matches[0].pii_type == "credit_card"

    def test_detect_email(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"email"}))
        detector = PIIDetector(config)
        matches = detector.scan("Contact me at user@example.com")
        assert len(matches) == 1
        assert matches[0].pii_type == "email"

    def test_detect_phone(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"phone"}))
        detector = PIIDetector(config)
        # With dashes
        matches = detector.scan("Call 123-456-7890")
        assert len(matches) == 1
        assert matches[0].pii_type == "phone"

    def test_detect_phone_parens(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"phone"}))
        detector = PIIDetector(config)
        matches = detector.scan("Call (123) 456-7890")
        assert len(matches) == 1
        assert matches[0].pii_type == "phone"

    def test_detect_ip_address(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ip_address"}))
        detector = PIIDetector(config)
        matches = detector.scan("Server IP: 192.168.1.1")
        assert len(matches) == 1
        assert matches[0].pii_type == "ip_address"

    def test_detect_multiple_types(self) -> None:
        config = PIIDetectorConfig(
            enabled=True,
            patterns=frozenset({"ssn", "email", "credit_card"})
        )
        detector = PIIDetector(config)
        text = "SSN: 123-45-6789, Email: test@example.com, Card: 1234-5678-9012-3456"
        matches = detector.scan(text)
        assert len(matches) == 3
        types = {m.pii_type for m in matches}
        assert types == {"ssn", "email", "credit_card"}

    def test_contains_pii_true(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn"}))
        detector = PIIDetector(config)
        assert detector.contains_pii("My SSN is 123-45-6789") is True

    def test_contains_pii_false(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn"}))
        detector = PIIDetector(config)
        assert detector.contains_pii("No PII here") is False

    def test_match_positions(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn"}))
        detector = PIIDetector(config)
        text = "My SSN is 123-45-6789 and that's it"
        matches = detector.scan(text)
        assert len(matches) == 1
        # Verify positions are correct
        assert text[matches[0].start:matches[0].end] == "123-45-6789"

    def test_no_pii_in_clean_text(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn", "email", "credit_card"}))
        detector = PIIDetector(config)
        text = "Hello, this is a normal message without any sensitive data."
        assert detector.scan(text) == []
        assert detector.contains_pii(text) is False

    def test_scan_messages(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn"}))
        detector = PIIDetector(config)
        messages = [
            {"content": "Hello"},
            {"content": "My SSN is 123-45-6789"},
            {"content": "Goodbye"},
        ]
        results = detector.scan_messages(messages)
        assert 1 in results
        assert 0 not in results
        assert 2 not in results
        assert len(results[1]) == 1
        assert results[1][0].pii_type == "ssn"

    def test_scan_messages_disabled(self) -> None:
        config = PIIDetectorConfig(enabled=False)
        detector = PIIDetector(config)
        messages = [{"content": "My SSN is 123-45-6789"}]
        assert detector.scan_messages(messages) == {}

    def test_scan_messages_none_content(self) -> None:
        config = PIIDetectorConfig(enabled=True, patterns=frozenset({"ssn"}))
        detector = PIIDetector(config)
        messages = [
            {"content": None},
            {"content": "My SSN is 123-45-6789"},
        ]
        results = detector.scan_messages(messages)
        assert 0 not in results
        assert 1 in results


class TestPIIMatch:
    def test_pii_match_frozen(self) -> None:
        match = PIIMatch(pii_type="ssn", start=0, end=11)
        with pytest.raises(AttributeError):
            match.pii_type = "email"  # type: ignore[misc]
