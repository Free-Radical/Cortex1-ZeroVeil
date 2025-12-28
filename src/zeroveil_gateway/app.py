from __future__ import annotations

import os
import time
import uuid

from fastapi import FastAPI, Header, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from zeroveil_gateway.audit import AuditEvent, AuditLogger
from zeroveil_gateway.policy import Policy
from zeroveil_gateway.schemas import (
    ChatCompletionsRequest,
    ChatCompletionsResponse,
    Choice,
    ChoiceMessage,
    ErrorBody,
    ErrorResponse,
    Usage,
)


class GatewayError(Exception):
    def __init__(self, *, http_status: int, code: str, message: str, details: dict[str, object]):
        self.http_status = http_status
        self.code = code
        self.message = message
        self.details = details


def create_app() -> FastAPI:
    policy_path = os.getenv("ZEROVEIL_POLICY_PATH", "policies/default.json")
    api_key = os.getenv("ZEROVEIL_API_KEY")
    policy = Policy.load(policy_path)
    audit = AuditLogger(sink=policy.logging_sink, path=policy.logging_path)

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

        if api_key:
            if not authorization or not authorization.startswith("Bearer "):
                deny("unauthorized", "Missing bearer token", {"header": "Authorization"}, http=401)
            token = authorization.removeprefix("Bearer ").strip()
            if token != api_key:
                deny("unauthorized", "Invalid API key", {}, http=401)

        if not req.messages:
            deny("invalid_request", "messages must be non-empty", {"field": "messages"}, http=400)
        if len(req.messages) > policy.max_messages:
            deny(
                "policy_denied",
                "Too many messages",
                {"limit": policy.max_messages},
                http=403,
            )
        for i, msg in enumerate(req.messages):
            if len(msg.content) > policy.max_chars_per_message:
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

        return ChatCompletionsResponse(
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

    return app
