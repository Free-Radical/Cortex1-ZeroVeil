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
        "HTTP-Referer": "https://zeroveil.io",
        "X-Title": "ZeroVeil Gateway",
    },
)

# ZDR (zero data retention) provider settings that every outbound OpenRouter
# request must carry. These values always win: a caller-supplied "provider"
# block may add other keys, but it can never weaken zdr, data_collection or
# allow_fallbacks below what is enforced here.
ZDR_PROVIDER_SETTINGS: dict[str, object] = {
    "zdr": True,
    "data_collection": "deny",
    "allow_fallbacks": False,
}


def _merged_zdr_provider(client_provider: dict[str, object] | None) -> dict[str, object]:
    """Merge a caller-supplied provider block with the enforced ZDR settings.

    Any keys the caller supplies are kept (e.g. "order", "quantizations"),
    but zdr / data_collection / allow_fallbacks are always forced to the
    enforced values, regardless of what the caller sent for them.
    """
    merged: dict[str, object] = dict(client_provider or {})
    merged.update(ZDR_PROVIDER_SETTINGS)
    return merged


class OpenRouterProvider(ProviderAdapter):
    """OpenRouter LLM provider adapter."""

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config or OPENROUTER_CONFIG)

    def chat_completions(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        provider: dict[str, object] | None = None,
    ) -> ProviderResponse:
        """Send chat completion request to OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model to use. If None, uses config.default_model.
            provider: Optional caller-supplied OpenRouter "provider" block
                (e.g. routing preferences). The gateway's ZDR enforcement
                (zdr=True, data_collection="deny", allow_fallbacks=False)
                always overrides these three keys in the merged block; other
                caller-supplied keys are preserved as-is.

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
            "provider": _merged_zdr_provider(provider),
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
