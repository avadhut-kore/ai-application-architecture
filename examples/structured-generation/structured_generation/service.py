"""Application service demonstrating structured generation and untrusted output validation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from contracts.models import CompletionRequest
from contracts.ports import TextGenerationPort
from contracts.validation import ValidationResult

from .models import (
    CustomerFeedbackExtraction,
    FeedbackCategory,
    FeedbackSentiment,
    FeedbackUrgency,
)

SYSTEM_PROMPT = """You are a precision enterprise text classification assistant.
Extract structured customer feedback into a strict JSON object adhering exactly to this schema:
{
  "category": "bug" | "feature_request" | "inquiry" | "billing",
  "sentiment": "positive" | "neutral" | "negative",
  "urgency": "low" | "medium" | "high" | "critical",
  "summary": "concise summary string",
  "confidence": float between 0.0 and 1.0
}

Respond ONLY with the JSON object. Do not include markdown preamble, commentary, or postscript."""

JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class FeedbackExtractionService:
    """Enterprise application use case demonstrating structured AI output extraction.

    Accepts any TextGenerationPort implementation (e.g. OllamaAdapter, cloud adapter, or test double).
    Enforces the Untrusted Model Output Principle: raw text is parsed and validated into strongly typed
    domain entities before being admitted into application workflows.
    """

    def __init__(
        self,
        client: TextGenerationPort,
        model: str = "llama3.2",
        max_corrective_retries: int = 1,
    ) -> None:
        self.client = client
        self.model = model
        self.max_corrective_retries = max_corrective_retries

    def _extract_json_string(self, raw_text: str) -> str:
        """Extract a JSON object substring, stripping surrounding markdown fences if present."""
        cleaned = raw_text.strip()

        # Check for ```json { ... } ``` block
        match = JSON_BLOCK_PATTERN.search(cleaned)
        if match:
            return match.group(1).strip()

        # Fallback: extract substring between first '{' and last '}'
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            return cleaned[start_idx : end_idx + 1].strip()

        return cleaned

    def validate_output(self, raw_text: str) -> ValidationResult[CustomerFeedbackExtraction]:
        """Validate raw, untrusted model text against the CustomerFeedbackExtraction schema."""
        errors: List[str] = []
        json_str = self._extract_json_string(raw_text)

        try:
            payload = json.loads(json_str)
        except (json.JSONDecodeError, Exception) as ex:
            return ValidationResult.failure(
                errors=[f"Malformed JSON syntax: {ex}"],
                raw_text=raw_text,
            )

        if not isinstance(payload, dict):
            return ValidationResult.failure(
                errors=[f"Expected JSON object, got {type(payload).__name__}"],
                raw_text=raw_text,
            )

        # 1. Category validation
        raw_category = payload.get("category")
        category: Optional[FeedbackCategory] = None
        if not raw_category:
            errors.append("Missing required field: 'category'")
        else:
            try:
                category = FeedbackCategory(str(raw_category).lower())
            except ValueError:
                allowed = [c.value for c in FeedbackCategory]
                errors.append(f"Invalid 'category': {raw_category!r}. Must be one of {allowed}")

        # 2. Sentiment validation
        raw_sentiment = payload.get("sentiment")
        sentiment: Optional[FeedbackSentiment] = None
        if not raw_sentiment:
            errors.append("Missing required field: 'sentiment'")
        else:
            try:
                sentiment = FeedbackSentiment(str(raw_sentiment).lower())
            except ValueError:
                allowed = [s.value for s in FeedbackSentiment]
                errors.append(f"Invalid 'sentiment': {raw_sentiment!r}. Must be one of {allowed}")

        # 3. Urgency validation
        raw_urgency = payload.get("urgency")
        urgency: Optional[FeedbackUrgency] = None
        if not raw_urgency:
            errors.append("Missing required field: 'urgency'")
        else:
            try:
                urgency = FeedbackUrgency(str(raw_urgency).lower())
            except ValueError:
                allowed = [u.value for u in FeedbackUrgency]
                errors.append(f"Invalid 'urgency': {raw_urgency!r}. Must be one of {allowed}")

        # 4. Summary validation
        summary = payload.get("summary")
        if not summary or not isinstance(summary, str) or not summary.strip():
            errors.append("Field 'summary' must be a non-empty string")

        # 5. Confidence validation
        confidence = payload.get("confidence")
        if confidence is None:
            errors.append("Missing required field: 'confidence'")
        elif not isinstance(confidence, (int, float)):
            errors.append(f"Field 'confidence' must be a float between 0.0 and 1.0, got {type(confidence).__name__}")
        elif not (0.0 <= float(confidence) <= 1.0):
            errors.append(f"Field 'confidence' must be between 0.0 and 1.0, got {confidence}")

        if errors or category is None or sentiment is None or urgency is None or not summary or confidence is None:
            return ValidationResult.failure(errors=errors, raw_text=raw_text)

        return ValidationResult.success(
            data=CustomerFeedbackExtraction(
                category=category,
                sentiment=sentiment,
                urgency=urgency,
                summary=summary.strip(),
                confidence=float(confidence),
            ),
            raw_text=raw_text,
        )

    async def extract_feedback(self, text: str) -> ValidationResult[CustomerFeedbackExtraction]:
        """Extract structured domain feedback from raw text with bounded corrective retry."""
        user_prompt = f"Extract structured feedback from this customer message:\n\n\"{text}\""
        request = CompletionRequest(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            model=self.model,
            temperature=0.0,
            metadata={"format": "json"},
        )

        response = await self.client.generate(request)
        result = self.validate_output(response.text)

        # Bounded corrective retry if model output fails schema validation
        retry_count = 0
        while not result.is_valid and retry_count < self.max_corrective_retries:
            retry_count += 1
            corrective_prompt = (
                f"Your previous JSON output was invalid for the following reasons:\n"
                f"- " + "\n- ".join(result.errors) + "\n\n"
                f"Previous raw output was:\n{response.text}\n\n"
                f"Please fix all errors and return ONLY the valid JSON object adhering to the schema."
            )
            corrective_request = CompletionRequest(
                prompt=corrective_prompt,
                system_prompt=SYSTEM_PROMPT,
                model=self.model,
                temperature=0.0,
                metadata={"format": "json", "is_corrective_retry": True},
            )
            response = await self.client.generate(corrective_request)
            result = self.validate_output(response.text)

        return result
