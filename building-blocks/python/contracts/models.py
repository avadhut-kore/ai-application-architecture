"""Domain data structures and models for AI operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence


class FinishReason(str, Enum):
    """Reason for completion termination."""

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    OTHER = "other"


class Role(str, Enum):
    """Role associated with a conversational turn."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ChatMessage:
    """A single turn in a conversational interaction."""

    role: Role
    content: str
    name: Optional[str] = None


@dataclass(frozen=True)
class UsageMetrics:
    """Token consumption metrics for an AI generation operation."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        if self.input_tokens < 0:
            raise ValueError("input_tokens cannot be negative")
        if self.output_tokens < 0:
            raise ValueError("output_tokens cannot be negative")
        if self.total_tokens == 0 and (self.input_tokens > 0 or self.output_tokens > 0):
            object.__setattr__(self, "total_tokens", self.input_tokens + self.output_tokens)
        elif self.total_tokens < (self.input_tokens + self.output_tokens):
            raise ValueError("total_tokens cannot be less than sum of input and output tokens")


@dataclass(frozen=True)
class CompletionRequest:
    """Request payload for model text generation."""

    prompt: str
    model: str
    system_prompt: Optional[str] = None
    messages: Optional[Sequence[ChatMessage]] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: Optional[Sequence[str]] = None
    metadata: Optional[Mapping[str, Any]] = field(default=None)

    def __post_init__(self) -> None:
        if not self.prompt and not self.messages:
            raise ValueError("CompletionRequest must specify non-empty prompt or messages")
        if not self.model:
            raise ValueError("CompletionRequest must specify a model identifier")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {self.temperature}")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive if specified, got {self.max_tokens}")


@dataclass(frozen=True)
class CompletionResponse:
    """Response payload resulting from model text generation."""

    text: str
    model: str
    finish_reason: FinishReason = FinishReason.STOP
    usage: Optional[UsageMetrics] = None
    latency_ms: Optional[float] = None
    metadata: Optional[Mapping[str, Any]] = field(default=None)
