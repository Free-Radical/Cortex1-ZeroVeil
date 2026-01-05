from __future__ import annotations

import os
import time
import uuid

from fastapi import FastAPI, Header, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from zeroveil_gateway.audit import AuditEvent, AuditLogger
from zeroveil_gateway.pii import PIIDetector
from zeroveil_gateway.policy import Policy
from zeroveil_gateway.schemas import (
    ALLOWED_ROLES,
    ChatCompletionsRequest,
    ChatCompletionsResponse,
    Choice,
    ChoiceMessage,
    ErrorBody,
    ErrorResponse,
    Usage,
)
from zeroveil_gateway.tenants import TenantRegistry


class GatewayError(Exception):
    def __init__(self, *, http_status: int, code: str, message: str, details: dict[str, object]):
        self.http_status = http_status
        self.code = code
        self.message = message
        self.details = details


def create_app() -> FastAPI:
    policy_path = os.getenv("ZEROVEIL_POLICY_PATH", "policies/default.json")
    tenants_path = os.getenv("ZEROVEIL_TENANTS_PATH", "tenants/default.json")
    legacy_api_key = os.getenv("ZEROVEIL_API_KEY")  # Deprecated: use tenants config
    policy = Policy.load(policy_path)
    audit = AuditLogger(sink=policy.logging_sink, path=policy.logging_path)
    pii_detector = PIIDetector(policy.pii_gate)

    # Load tenant registry if config exists, otherwise None (legacy mode)
    registry: TenantRegistry | None = None
    try:
        registry = TenantRegistry.load(tenants_path)
    except (FileNotFoundError, ValueError):
        # Fall back to legacy single-key mode if tenants config missing/invalid
        pass

    app = FastAPI(title="ZeroVeil Gateway (Community)", version=policy.version)

    @app.exception_handler(GatewayError)
    def handle_gateway_error(_request, exc: GatewayError):  # type: ignore[no-untyped-def]
        return JSONResponse(
            status_code=exc.http_status,
            content=ErrorResponse(
                error=ErrorBody(code=exc.code, message=exc.message, details=exc.details),
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(_request, exc: RequestValidationError):  # type: ignore[no-untyped-def]
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorBody(
                    code="invalid_request",
                    message="Invalid request body",
                    details={"errors": exc.errors()},
                )
            ).model_dump(),
        )

    @app.get("/healthz")
    def healthz() -> dict[str, bool]:
        return {"ok": True}

    @app.post(
        "/v1/chat/completions",
        response_model=ChatCompletionsResponse,
        responses={
            400: {"model": ErrorResponse},
            401: {"model": ErrorResponse},
            403: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )
    def chat_completions(
        req: ChatCompletionsRequest,
        response: Response,
        authorization: str | None = Header(default=None),
        x_zeroveil_tenant: str | None = Header(default=None),
    ) -> ChatCompletionsResponse:
        started = time.time()
        request_id = f"zv_{uuid.uuid4().hex[:16]}"
        tenant_id = x_zeroveil_tenant or "default"

        def deny(code: str, message: str, details: dict[str, object] | None = None, *, http: int) -> None:
            audit.log(
                AuditEvent.now(
                    request_id=request_id,
                    tenant_id=tenant_id,
                    action="deny",
                    reason=code,
                    provider=None,
                    model=req.model,
                    message_count=len(req.messages or []),
                    total_chars=sum(len(m.content or "") for m in (req.messages or [])),
                    zdr_only=bool(req.zdr_only),
                    scrubbed_attested=bool(req.metadata.scrubbed),
                    latency_ms=int((time.time() - started) * 1000),
                    extra={"details": details or {}},
                )
            )
            raise GatewayError(
                http_status=http,
                code=code,
                message=message,
                details=details or {},
            )

        # Multi-tenant auth (preferred) or legacy single-key auth
        authenticated_tenant = None
        if registry is not None:
            if not authorization or not authorization.startswith("Bearer "):
                deny("unauthorized", "Missing bearer token", {"header": "Authorization"}, http=401)
            token = authorization.removeprefix("Bearer ").strip()
            authenticated_tenant = registry.authenticate(token)
            if authenticated_tenant is None:
                deny("unauthorized", "Invalid API key", {}, http=401)
            tenant_id = authenticated_tenant.tenant_id

            # Check rate limits
            if not registry.check_rate_limit(tenant_id):
                rpm_remaining = registry.rpm_remaining(tenant_id)
                tpd_remaining = registry.tpd_remaining(tenant_id)
                deny(
                    "rate_limited",
                    "Rate limit exceeded",
                    {"rpm_remaining": rpm_remaining, "tpd_remaining": tpd_remaining},
                    http=429,
                )
        elif legacy_api_key:
            # Legacy single-key mode (deprecated)
            if not authorization or not authorization.startswith("Bearer "):
                deny("unauthorized", "Missing bearer token", {"header": "Authorization"}, http=401)
            token = authorization.removeprefix("Bearer ").strip()
            if token != legacy_api_key:
                deny("unauthorized", "Invalid API key", {}, http=401)

        if not req.messages:
            deny("invalid_request", "messages must be non-empty", {"field": "messages"}, http=400)

        for i, msg in enumerate(req.messages):
            if msg.role not in ALLOWED_ROLES:
                deny(
                    "invalid_request",
                    "Invalid message role",
                    {"field": f"messages[{i}].role", "value": msg.role, "allowed": list(ALLOWED_ROLES)},
                    http=400,
                )

        # PII gate: reject requests containing detected PII patterns
        if pii_detector.config.enabled:
            for i, msg in enumerate(req.messages):
                content = msg.content or ""
                matches = pii_detector.scan(content)
                if matches:
                    # Report types detected but NOT the actual content
                    detected_types = list({m.pii_type for m in matches})
                    deny(
                        "pii_detected",
                        "Request contains unscrubbed PII. Scrub before retry.",
                        {"field": f"messages[{i}].content", "detected_types": detected_types},
                        http=403,
                    )

        if len(req.messages) > policy.max_messages:
            deny(
                "policy_denied",
                "Too many messages",
                {"limit": policy.max_messages},
                http=403,
            )

        if policy.allowed_models and "*" not in policy.allowed_models and req.model is not None:
            if req.model not in policy.allowed_models:
                deny(
                    "policy_denied",
                    "Model not allowed by policy",
                    {"field": "model", "value": req.model, "allowed": policy.allowed_models},
                    http=403,
                )
        for i, msg in enumerate(req.messages):
            if len(msg.content or "") > policy.max_chars_per_message:
                deny(
                    "policy_denied",
                    "Message too large",
                    {"index": i, "limit": policy.max_chars_per_message},
                    http=403,
                )

        if policy.enforce_zdr_only and not req.zdr_only:
            deny("policy_denied", "zdr_only must be true", {"field": "zdr_only"}, http=403)

        if policy.require_scrubbed_attestation and not req.metadata.scrubbed:
            deny(
                "policy_denied",
                "Scrub attestation required (metadata.scrubbed=true). ZeroVeil does not scrub content server-side.",
                {"field": "metadata.scrubbed"},
                http=403,
            )

        for i, msg in enumerate(req.messages):
            if msg.content is None:
                deny(
                    "invalid_request",
                    "messages[i].content must be a string",
                    {"field": f"messages[{i}].content"},
                    http=400,
                )
            if "\x00" in msg.content:
                deny(
                    "invalid_request",
                    "messages[i].content contains null bytes",
                    {"field": f"messages[{i}].content"},
                    http=400,
                )

        # Provider/model routing is stubbed in v0 (Week 1).
        selected_provider = policy.allowed_providers[0]
        selected_model = req.model or "stub"

        audit.log(
            AuditEvent.now(
                request_id=request_id,
                tenant_id=tenant_id,
                action="allow",
                reason="ok",
                provider=selected_provider,
                model=selected_model,
                message_count=len(req.messages),
                total_chars=sum(len(m.content) for m in req.messages),
                zdr_only=bool(req.zdr_only),
                scrubbed_attested=bool(req.metadata.scrubbed),
                latency_ms=int((time.time() - started) * 1000),
                extra={"policy_version": policy.version},
            )
        )

        # Add rate limit headers if using multi-tenant auth
        if registry is not None and authenticated_tenant is not None:
            rpm_remaining = registry.rpm_remaining(tenant_id)
            tpd_remaining = registry.tpd_remaining(tenant_id)
            if rpm_remaining is not None:
                response.headers["X-RateLimit-Remaining-RPM"] = str(rpm_remaining)
            if tpd_remaining is not None:
                response.headers["X-RateLimit-Remaining-TPD"] = str(tpd_remaining)

        resp = ChatCompletionsResponse(
            id=request_id,
            object="chat.completion",
            created=int(time.time()),
            model=selected_model,
            choices=[
                Choice(
                    index=0,
                    message=ChoiceMessage(role="assistant", content="stubbed_response"),
                    finish_reason="stop",
                )
            ],
            usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        )

        # Record token usage for rate limiting (v0: stubbed at 0)
        if registry is not None and authenticated_tenant is not None:
            registry.record_usage(tenant_id, resp.usage.total_tokens)

        return resp

    return app
