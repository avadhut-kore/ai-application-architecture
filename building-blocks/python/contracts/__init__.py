"""Bounded minimum core contracts for enterprise AI applications."""

from .errors import (
    AiAuthenticationError,
    AiContentFilterError,
    AiError,
    AiInvalidRequestError,
    AiModelNotFoundError,
    AiNonTransientError,
    AiProviderUnavailableError,
    AiRateLimitError,
    AiSchemaValidationError,
    AiSemanticError,
    AiTimeoutError,
    AiTransientError,
)
from .evaluation import (
    EvaluationMetric,
    EvaluationScenarioResult,
    EvaluationStatus,
    EvaluationSummary,
)
from .models import (
    ChatMessage,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    FinishReason,
    Role,
    UsageMetrics,
)
from .ports import (
    EmbeddingPort,
    IEmbeddingClient,
    ILlmClient,
    LlmClientPort,
    TextGenerationPort,
)
from .telemetry import (
    GEN_AI_OPERATION_NAME,
    GEN_AI_REQUEST_MAX_TOKENS,
    GEN_AI_REQUEST_MODEL,
    GEN_AI_REQUEST_TEMPERATURE,
    GEN_AI_RESPONSE_FINISH_REASONS,
    GEN_AI_SYSTEM,
    GEN_AI_USAGE_INPUT_TOKENS,
    GEN_AI_USAGE_OUTPUT_TOKENS,
    AiOperationContext,
)
from .validation import ValidationResult

__all__ = [
    # Models
    "ChatMessage",
    "CompletionRequest",
    "CompletionResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "FinishReason",
    "Role",
    "UsageMetrics",
    # Ports
    "TextGenerationPort",
    "LlmClientPort",
    "ILlmClient",
    "EmbeddingPort",
    "IEmbeddingClient",
    # Telemetry
    "AiOperationContext",
    "GEN_AI_OPERATION_NAME",
    "GEN_AI_REQUEST_MAX_TOKENS",
    "GEN_AI_REQUEST_MODEL",
    "GEN_AI_REQUEST_TEMPERATURE",
    "GEN_AI_RESPONSE_FINISH_REASONS",
    "GEN_AI_SYSTEM",
    "GEN_AI_USAGE_INPUT_TOKENS",
    "GEN_AI_USAGE_OUTPUT_TOKENS",
    # Errors
    "AiError",
    "AiTransientError",
    "AiRateLimitError",
    "AiTimeoutError",
    "AiProviderUnavailableError",
    "AiNonTransientError",
    "AiAuthenticationError",
    "AiInvalidRequestError",
    "AiModelNotFoundError",
    "AiSemanticError",
    "AiSchemaValidationError",
    "AiContentFilterError",
    # Validation
    "ValidationResult",
    # Evaluation
    "EvaluationMetric",
    "EvaluationScenarioResult",
    "EvaluationStatus",
    "EvaluationSummary",
]
