"""OpenRouter provider adapter."""

from __future__ import annotations

import httpx

from zeroveil_gateway.providers.base import (
    ProviderAdapter,
    ProviderConfig,
    ProviderError,
    ProviderResponse,
)


# Default OpenRouter configuration
OPENROUTER_CONFIG = ProviderConfig(
    name="openrouter",
    api_key_env="OPENROUTER_API_KEY",
    base_url="https://openrouter.ai/api",
    default_model="meta-llama/llama-3.1-8b-instruct",
    timeout_seconds=30,
    extra_headers={
        "HTTP-Referer": "https://zeroveil.dev",
        "X-Title": "ZeroVeil Gateway",
    },
)


class OpenRouterProvider(ProviderAdapter):
    """OpenRouter LLM provider adapter."""

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config or OPENROUTER_CONFIG)

    def chat_completions(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> ProviderResponse:
        """Send chat completion request to OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model to use. If None, uses config.default_model.

        Returns:
            ProviderResponse with content and token usage.

        Raises:
            ProviderError: If the request fails.
        """
        self.validate_config()

        url = f"{self.config.base_url}/v1/chat/completions"
        selected_model = model or self.config.default_model

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            **self.config.extra_headers,
        }

        payload = {
            "model": selected_model,
            "messages": messages,
        }

        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    # Try to extract error details from response
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", response.text)
                    except Exception:
                        error_msg = response.text

                    raise ProviderError(
                        f"OpenRouter request failed: {error_msg}",
                        status_code=response.status_code,
                        details={"response": response.text[:500]},
                    )

                data = response.json()

        except httpx.TimeoutException as e:
            raise ProviderError(
                f"OpenRouter request timed out after {self.config.timeout_seconds}s",
                details={"timeout": self.config.timeout_seconds},
            ) from e
        except httpx.RequestError as e:
            raise ProviderError(
                f"OpenRouter request failed: {e}",
                details={"error_type": type(e).__name__},
            ) from e

        # Extract response data
        choices = data.get("choices") or []
        if not choices:
            raise ProviderError(
                "OpenRouter returned empty choices",
                details={"response": data},
            )

        choice = choices[0]
        message = choice.get("message", {})
        content = message.get("content", "")

        usage = data.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        return ProviderResponse(
            content=content,
            model=data.get("model", selected_model),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )
