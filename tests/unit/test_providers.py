"""Tests for LLM provider adapters."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from zeroveil_gateway.providers import (
    ProviderAdapter,
    ProviderConfig,
    ProviderError,
    ProviderResponse,
    OpenRouterProvider,
)
from zeroveil_gateway.providers.openrouter import OPENROUTER_CONFIG


class TestProviderConfig:
    """Tests for ProviderConfig."""

    def test_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API key should be read from environment variable."""
        monkeypatch.setenv("TEST_API_KEY", "sk-test-123")
        config = ProviderConfig(
            name="test",
            api_key_env="TEST_API_KEY",
            base_url="https://test.api",
            default_model="test-model",
        )
        assert config.api_key == "sk-test-123"

    def test_api_key_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API key should be None when env var not set."""
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        config = ProviderConfig(
            name="test",
            api_key_env="TEST_API_KEY",
            base_url="https://test.api",
            default_model="test-model",
        )
        assert config.api_key is None

    def test_default_timeout(self) -> None:
        """Default timeout should be 30 seconds."""
        config = ProviderConfig(
            name="test",
            api_key_env="TEST_API_KEY",
            base_url="https://test.api",
            default_model="test-model",
        )
        assert config.timeout_seconds == 30


class TestProviderResponse:
    """Tests for ProviderResponse."""

    def test_response_fields(self) -> None:
        """Response should contain all required fields."""
        response = ProviderResponse(
            content="Hello, world!",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )
        assert response.content == "Hello, world!"
        assert response.model == "test-model"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5
        assert response.total_tokens == 15
        assert response.finish_reason == "stop"

    def test_custom_finish_reason(self) -> None:
        """Finish reason should be customizable."""
        response = ProviderResponse(
            content="",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
            finish_reason="length",
        )
        assert response.finish_reason == "length"


class TestProviderError:
    """Tests for ProviderError."""

    def test_error_with_status_code(self) -> None:
        """Error should include status code."""
        error = ProviderError("Request failed", status_code=401)
        assert str(error) == "Request failed"
        assert error.status_code == 401

    def test_error_with_details(self) -> None:
        """Error should include details dict."""
        error = ProviderError(
            "Request failed",
            status_code=400,
            details={"field": "model", "value": "invalid"},
        )
        assert error.details == {"field": "model", "value": "invalid"}

    def test_error_defaults(self) -> None:
        """Error should have sensible defaults."""
        error = ProviderError("Something went wrong")
        assert error.status_code is None
        assert error.details == {}


class TestOpenRouterProvider:
    """Tests for OpenRouterProvider."""

    def test_default_config(self) -> None:
        """Provider should use default OpenRouter config."""
        provider = OpenRouterProvider()
        assert provider.config.name == "openrouter"
        assert provider.config.api_key_env == "OPENROUTER_API_KEY"
        assert provider.config.base_url == "https://openrouter.ai/api"

    def test_custom_config(self) -> None:
        """Provider should accept custom config."""
        custom_config = ProviderConfig(
            name="custom-openrouter",
            api_key_env="CUSTOM_API_KEY",
            base_url="https://custom.openrouter.ai/api",
            default_model="custom-model",
            timeout_seconds=60,
        )
        provider = OpenRouterProvider(custom_config)
        assert provider.config.name == "custom-openrouter"
        assert provider.config.timeout_seconds == 60

    def test_validate_config_missing_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Validation should fail when API key is missing."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        provider = OpenRouterProvider()
        with pytest.raises(ProviderError) as exc_info:
            provider.validate_config()
        assert "OPENROUTER_API_KEY" in str(exc_info.value)

    def test_validate_config_with_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Validation should pass when API key is set."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-123")
        provider = OpenRouterProvider()
        provider.validate_config()  # Should not raise

    @patch("zeroveil_gateway.providers.openrouter.request_with_backoff")
    def test_chat_completions_success(
        self, mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Successful chat completion should return ProviderResponse."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-123")

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "model": "meta-llama/llama-3.1-8b-instruct",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        mock_request.return_value = mock_response

        provider = OpenRouterProvider()
        response = provider.chat_completions(
            messages=[{"role": "user", "content": "Hi"}]
        )

        assert response.content == "Hello!"
        assert response.model == "meta-llama/llama-3.1-8b-instruct"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5
        assert response.total_tokens == 15
        assert response.finish_reason == "stop"

    @patch("zeroveil_gateway.providers.openrouter.request_with_backoff")
    def test_chat_completions_uses_default_model(
        self, mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completion should use default model when not specified."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "choices": [{"message": {"content": "Hi"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

        mock_request.return_value = mock_response

        provider = OpenRouterProvider()
        provider.chat_completions(messages=[{"role": "user", "content": "Hi"}])

        # Check that default model was used in request
        call_args = mock_request.call_args
        payload = call_args.kwargs["json"]
        assert payload["model"] == OPENROUTER_CONFIG.default_model

    @patch("zeroveil_gateway.providers.openrouter.request_with_backoff")
    def test_chat_completions_api_error(
        self, mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """API error should raise ProviderError with status code."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-123")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = {
            "error": {"message": "Invalid API key"}
        }

        mock_request.return_value = mock_response

        provider = OpenRouterProvider()
        with pytest.raises(ProviderError) as exc_info:
            provider.chat_completions(messages=[{"role": "user", "content": "Hi"}])

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    @patch("zeroveil_gateway.providers.openrouter.request_with_backoff")
    def test_chat_completions_empty_choices(
        self, mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty choices should raise ProviderError."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "test-model",
            "choices": [],
            "usage": {"prompt_tokens": 1, "completion_tokens": 0, "total_tokens": 1},
        }

        mock_request.return_value = mock_response

        provider = OpenRouterProvider()
        with pytest.raises(ProviderError) as exc_info:
            provider.chat_completions(messages=[{"role": "user", "content": "Hi"}])

        assert "empty choices" in str(exc_info.value).lower()
