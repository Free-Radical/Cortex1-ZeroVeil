from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TenantConfig:
    tenant_id: str
    api_keys: list[str]
    rate_limit_rpm: int
    rate_limit_tpd: int
    enabled: bool

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id must be non-empty")
        if self.rate_limit_rpm < 0:
            raise ValueError("rate_limit_rpm must be >= 0")
        if self.rate_limit_tpd < 0:
            raise ValueError("rate_limit_tpd must be >= 0")
        if not isinstance(self.api_keys, list):
            raise ValueError("api_keys must be a list")
        for key_hash in self.api_keys:
            if not isinstance(key_hash, str):
                raise ValueError("api_keys must contain strings")
            normalized = key_hash.strip().lower()
            if len(normalized) != 64:
                raise ValueError("api_keys entries must be sha256 hex digests")
            if any(ch not in "0123456789abcdef" for ch in normalized):
                raise ValueError("api_keys entries must be sha256 hex digests")


class TenantRegistry:
    def __init__(
        self,
        tenants: dict[str, TenantConfig],
        *,
        now: Any | None = None,
    ) -> None:
        self._tenants = dict(tenants)
        self._now = now if now is not None else time.time

        self._requests_by_tenant: dict[str, Deque[float]] = {}
        self._tokens_by_tenant: dict[str, Deque[tuple[float, int]]] = {}

    @property
    def tenants(self) -> dict[str, TenantConfig]:
        return dict(self._tenants)

    def get(self, tenant_id: str) -> TenantConfig | None:
        return self._tenants.get(tenant_id)

    @classmethod
    def load(cls, path: str) -> TenantRegistry:
        parsed_path = Path(path)
        raw = parsed_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid tenants JSON: {exc}") from exc

        if not isinstance(data, dict) or "tenants" not in data:
            raise ValueError("Tenants JSON must be an object with a 'tenants' key")
        tenants_raw = data["tenants"]
        if not isinstance(tenants_raw, list):
            raise ValueError("'tenants' must be a list")

        tenants: dict[str, TenantConfig] = {}
        for entry in tenants_raw:
            if not isinstance(entry, dict):
                raise ValueError("Each tenant entry must be an object")
            tenant_id = entry.get("tenant_id")
            api_key_hashes = entry.get("api_key_hashes")
            rate_limit_rpm = entry.get("rate_limit_rpm", 0)
            rate_limit_tpd = entry.get("rate_limit_tpd", 0)
            enabled = entry.get("enabled", True)

            if not isinstance(tenant_id, str):
                raise ValueError("tenant_id must be a string")
            if not isinstance(api_key_hashes, list) or not all(
                isinstance(x, str) for x in api_key_hashes
            ):
                raise ValueError("api_key_hashes must be a list of strings")
            if not isinstance(rate_limit_rpm, int):
                raise ValueError("rate_limit_rpm must be an int")
            if not isinstance(rate_limit_tpd, int):
                raise ValueError("rate_limit_tpd must be an int")
            if not isinstance(enabled, bool):
                raise ValueError("enabled must be a bool")

            normalized_hashes = [h.strip().lower() for h in api_key_hashes]
            tenant = TenantConfig(
                tenant_id=tenant_id,
                api_keys=normalized_hashes,
                rate_limit_rpm=rate_limit_rpm,
                rate_limit_tpd=rate_limit_tpd,
                enabled=enabled,
            )
            if tenant.tenant_id in tenants:
                raise ValueError(f"Duplicate tenant_id: {tenant.tenant_id}")
            tenants[tenant.tenant_id] = tenant

        return cls(tenants)

    def authenticate(self, bearer_token: str) -> TenantConfig | None:
        token = bearer_token.strip()
        if not token:
            return None

        token_hash = sha256_hex(token)
        matched: TenantConfig | None = None

        for tenant in self._tenants.values():
            for candidate in tenant.api_keys:
                is_match = secrets.compare_digest(token_hash, candidate)
                if is_match and tenant.enabled:
                    matched = tenant

        return matched

    def _prune_requests(self, tenant_id: str, now: float) -> Deque[float]:
        window_start = now - 60.0
        dq = self._requests_by_tenant.setdefault(tenant_id, deque())
        while dq and dq[0] <= window_start:
            dq.popleft()
        return dq

    def _prune_tokens(self, tenant_id: str, now: float) -> Deque[tuple[float, int]]:
        window_start = now - 86400.0
        dq = self._tokens_by_tenant.setdefault(tenant_id, deque())
        while dq and dq[0][0] <= window_start:
            dq.popleft()
        return dq

    def rpm_remaining(self, tenant_id: str) -> int | None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None or not tenant.enabled:
            return 0
        if tenant.rate_limit_rpm == 0:
            return None

        now = float(self._now())
        dq = self._prune_requests(tenant_id, now)
        return max(0, tenant.rate_limit_rpm - len(dq))

    def tpd_remaining(self, tenant_id: str) -> int | None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None or not tenant.enabled:
            return 0
        if tenant.rate_limit_tpd == 0:
            return None

        now = float(self._now())
        dq = self._prune_tokens(tenant_id, now)
        used = sum(tokens for _, tokens in dq)
        return max(0, tenant.rate_limit_tpd - used)

    def check_rate_limit(self, tenant_id: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if tenant is None or not tenant.enabled:
            return False

        now = float(self._now())

        if tenant.rate_limit_tpd != 0:
            tokens_remaining = self.tpd_remaining(tenant_id)
            if tokens_remaining is not None and tokens_remaining <= 0:
                return False

        if tenant.rate_limit_rpm == 0:
            return True

        dq = self._prune_requests(tenant_id, now)
        if len(dq) >= tenant.rate_limit_rpm:
            return False
        dq.append(now)
        return True

    def record_usage(self, tenant_id: str, tokens: int) -> None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None or not tenant.enabled:
            return
        if tokens < 0:
            raise ValueError("tokens must be >= 0")
        if tenant.rate_limit_tpd == 0:
            return

        now = float(self._now())
        dq = self._prune_tokens(tenant_id, now)
        dq.append((now, tokens))
