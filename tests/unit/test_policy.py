from __future__ import annotations

import pytest

from zeroveil_gateway.policy import Policy, PolicyError


def test_policy_from_dict_defaults_and_required_fields() -> None:
    policy = Policy.from_dict(
        {
            "version": "0",
            "allowed_providers": ["openrouter"],
            "logging": {"mode": "metadata_only", "sink": "stdout"},
        }
    )
    assert policy.enforce_zdr_only is True
    assert policy.require_scrubbed_attestation is True
    assert policy.allowed_models == ["*"]


def test_policy_rejects_missing_allowed_providers() -> None:
    with pytest.raises(PolicyError, match="allowed_providers must be non-empty"):
        Policy.from_dict({"logging": {"mode": "metadata_only", "sink": "stdout"}})


def test_policy_rejects_unsupported_logging_mode() -> None:
    with pytest.raises(PolicyError, match="Unsupported logging\\.mode"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {"mode": "content", "sink": "stdout"},
            }
        )


def test_policy_requires_path_for_jsonl_sink() -> None:
    with pytest.raises(PolicyError, match="logging\\.path required"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {"mode": "metadata_only", "sink": "jsonl"},
            }
        )

