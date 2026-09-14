"""Bounded domain error taxonomy for AI operations."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence


class AiError(Exception):
    """Base exception for all AI domain and operational errors."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "AI_ERROR",
        is_transient: bool = False,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.is_transient = is_transient
        self.details = dict(details) if details else {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code!r}, message={self.message!r}, transient={self.is_transient})"


# ---------------------------------------------------------------------------
# Transient / Retriable Errors
# ---------------------------------------------------------------------------


class AiTransientError(AiError):
    """Base for errors where a retry may succeed (e.g. rate limit, timeout)."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "AI_TRANSIENT_ERROR",
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, is_transient=True, details=details)


class AiRateLimitError(AiTransientError):
    """Upstream provider rate limit or quota exceeded."""

    def __init__(
        self,
        message: str = "AI provider rate limit exceeded",
        *,
        retry_after_seconds: Optional[float] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        err_details = dict(details) if details else {}
        if retry_after_seconds is not None:
            err_details["retry_after_seconds"] = retry_after_seconds
        super().__init__(message, error_code="AI_RATE_LIMIT", details=err_details)
        self.retry_after_seconds = retry_after_seconds


class AiTimeoutError(AiTransientError):
    """Operation timed out waiting for AI provider response."""

    def __init__(
        self,
        message: str = "AI operation timed out",
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="AI_TIMEOUT", details=details)


class AiProviderUnavailableError(AiTransientError):
    """AI provider or local inference engine is unreachable or temporarily down."""

    def __init__(
        self,
        message: str = "AI provider service is unavailable",
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="AI_PROVIDER_UNAVAILABLE", details=details)


# ---------------------------------------------------------------------------
# Non-Transient / Fatal Errors
# ---------------------------------------------------------------------------


class AiNonTransientError(AiError):
    """Base for errors where retrying will not succeed without changes."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "AI_NON_TRANSIENT_ERROR",
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, is_transient=False, details=details)


class AiAuthenticationError(AiNonTransientError):
    """Authentication or authorization failure against the provider."""

    def __init__(
        self,
        message: str = "Authentication failed for AI provider",
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="AI_AUTHENTICATION_ERROR", details=details)


class AiInvalidRequestError(AiNonTransientError):
    """Invalid request parameters, context length exceeded, or malformed input."""

    def __init__(
        self,
        message: str = "Invalid AI request parameters",
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="AI_INVALID_REQUEST", details=details)


class AiModelNotFoundError(AiNonTransientError):
    """Requested model identifier is not available or not installed."""

    def __init__(
        self,
        model_name: str,
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        err_details = dict(details) if details else {}
        err_details["model_name"] = model_name
        super().__init__(
            f"AI model not found: {model_name}",
            error_code="AI_MODEL_NOT_FOUND",
            details=err_details,
        )
        self.model_name = model_name


# ---------------------------------------------------------------------------
# Semantic Errors
# ---------------------------------------------------------------------------


class AiSemanticError(AiNonTransientError):
    """Base for errors relating to model output interpretation and policy compliance."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "AI_SEMANTIC_ERROR",
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class AiSchemaValidationError(AiSemanticError):
    """Model output failed structural parsing or schema validation."""

    def __init__(
        self,
        message: str = "Model output failed schema validation",
        *,
        raw_output: Optional[str] = None,
        validation_errors: Optional[Sequence[str]] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        err_details = dict(details) if details else {}
        if raw_output is not None:
            err_details["raw_output"] = raw_output
        if validation_errors is not None:
            err_details["validation_errors"] = list(validation_errors)
        super().__init__(message, error_code="AI_SCHEMA_VALIDATION_ERROR", details=err_details)
        self.raw_output = raw_output
        self.validation_errors = list(validation_errors) if validation_errors else []


class AiContentFilterError(AiSemanticError):
    """Model output was blocked or redacted due to content filtering or guardrail policies."""

    def __init__(
        self,
        message: str = "AI output blocked by content filter policy",
        *,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="AI_CONTENT_FILTER_ERROR", details=details)
