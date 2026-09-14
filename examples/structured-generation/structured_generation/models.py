"""Domain models and schemas for structured feedback extraction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FeedbackCategory(str, Enum):
    """Business classification of the customer feedback."""

    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    INQUIRY = "inquiry"
    BILLING = "billing"


class FeedbackSentiment(str, Enum):
    """Assessed emotional tone of the feedback."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FeedbackUrgency(str, Enum):
    """Operational urgency required for resolution."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CustomerFeedbackExtraction:
    """Strongly typed, validated domain entity extracted from raw feedback text."""

    category: FeedbackCategory
    sentiment: FeedbackSentiment
    urgency: FeedbackUrgency
    summary: str
    confidence: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not self.summary or not self.summary.strip():
            raise ValueError("summary cannot be empty")
