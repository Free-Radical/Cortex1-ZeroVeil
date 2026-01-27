"""Base provider interface for LLM backends."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ProviderError(Exception):
    """Error from LLM provider."""

    def __init__(self, message: str, *, status_code: int | None = None, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    api_key_env: str  # Environment variable name for API key
    base_url: str
    default_model: str
    timeout_seconds: int = 30
    extra_headers: dict[str, str] = field(default_factory=dict)

    @property
    def api_key(self) -> str | None:
        """Get API key from environment."""
        return os.getenv(self.api_key_env)


@dataclass
class ProviderResponse:
    """Response from LLM provider."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str = "stop"
    raw_response: dict[str, Any] | None = None


class ProviderAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @abstractmethod
    def chat_completions(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> ProviderResponse:
        """Send chat completion request to provider.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model to use. If None, uses config.default_model.

        Returns:
            ProviderResponse with content and token usage.

        Raises:
            ProviderError: If the request fails.
        """
        ...

    def validate_config(self) -> None:
        """Validate provider configuration.

        Raises:
            ProviderError: If configuration is invalid.
        """
        if not self.config.api_key:
            raise ProviderError(
                f"API key not found. Set {self.config.api_key_env} environment variable.",
                details={"env_var": self.config.api_key_env},
            )
