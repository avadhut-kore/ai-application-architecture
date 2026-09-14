"""Hermetic unit tests for FeedbackExtractionService structured extraction."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from typing import List, Optional

# Ensure paths
SCRIPT_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXAMPLE_DIR.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"

if str(BUILDING_BLOCKS_DIR) not in sys.path:
    sys.path.insert(0, str(BUILDING_BLOCKS_DIR))
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

from contracts.models import CompletionRequest, CompletionResponse, FinishReason, UsageMetrics
from contracts.ports import TextGenerationPort
from contracts.telemetry import AiOperationContext
from structured_generation.models import (
    FeedbackCategory,
    FeedbackSentiment,
    FeedbackUrgency,
)
from structured_generation.service import FeedbackExtractionService


class FakeLlmClient(TextGenerationPort):
    """In-memory deterministic test double for TextGenerationPort."""

    def __init__(self, responses: Optional[List[str]] = None) -> None:
        self.responses: List[str] = list(responses) if responses else []
        self.call_count: int = 0
        self.recorded_requests: List[CompletionRequest] = []

    async def generate(
        self,
        request: CompletionRequest,
        context: Optional[AiOperationContext] = None,
    ) -> CompletionResponse:
        self.call_count += 1
        self.recorded_requests.append(request)
        if self.responses:
            text = self.responses.pop(0)
        else:
            text = "{}"
        return CompletionResponse(
            text=text,
            model=request.model,
            finish_reason=FinishReason.STOP,
            usage=UsageMetrics(input_tokens=10, output_tokens=10),
            latency_ms=12.5,
        )


class TestFeedbackExtractionService(unittest.TestCase):
    """Test suite verifying structured extraction validation and corrective retries."""

    def test_successful_feedback_extraction(self) -> None:
        valid_json = (
            '{\n'
            '  "category": "bug",\n'
            '  "sentiment": "negative",\n'
            '  "urgency": "high",\n'
            '  "summary": "Application crashes on login",\n'
            '  "confidence": 0.95\n'
            '}'
        )
        fake_client = FakeLlmClient([valid_json])
        service = FeedbackExtractionService(client=fake_client)

        result = asyncio.run(service.extract_feedback("The app crashes whenever I click login."))

        self.assertTrue(result.is_valid)
        extraction = result.unwrap()
        self.assertEqual(extraction.category, FeedbackCategory.BUG)
        self.assertEqual(extraction.sentiment, FeedbackSentiment.NEGATIVE)
        self.assertEqual(extraction.urgency, FeedbackUrgency.HIGH)
        self.assertEqual(extraction.summary, "Application crashes on login")
        self.assertEqual(extraction.confidence, 0.95)
        self.assertEqual(fake_client.call_count, 1)

    def test_markdown_code_fence_handling(self) -> None:
        markdown_json = (
            'Here is the extracted information:\n'
            '```json\n'
            '{\n'
            '  "category": "feature_request",\n'
            '  "sentiment": "positive",\n'
            '  "urgency": "low",\n'
            '  "summary": "Request dark mode theme",\n'
            '  "confidence": 0.88\n'
            '}\n'
            '```\n'
            'Hope this helps!'
        )
        fake_client = FakeLlmClient([markdown_json])
        service = FeedbackExtractionService(client=fake_client)

        result = asyncio.run(service.extract_feedback("Please add dark mode! Love the app."))

        self.assertTrue(result.is_valid)
        extraction = result.unwrap()
        self.assertEqual(extraction.category, FeedbackCategory.FEATURE_REQUEST)
        self.assertEqual(extraction.sentiment, FeedbackSentiment.POSITIVE)

    def test_malformed_json_failure(self) -> None:
        malformed_text = "I am an AI and cannot classify this feedback."
        fake_client = FakeLlmClient([malformed_text, malformed_text])
        service = FeedbackExtractionService(client=fake_client, max_corrective_retries=1)

        result = asyncio.run(service.extract_feedback("Random text"))

        self.assertFalse(result.is_valid)
        self.assertTrue(any("Malformed JSON syntax" in err for err in result.errors))
        self.assertEqual(fake_client.call_count, 2)  # initial + 1 corrective retry

    def test_missing_field_failure(self) -> None:
        missing_category_json = (
            '{\n'
            '  "sentiment": "neutral",\n'
            '  "urgency": "low",\n'
            '  "summary": "Question about pricing",\n'
            '  "confidence": 0.9\n'
            '}'
        )
        fake_client = FakeLlmClient([missing_category_json, missing_category_json])
        service = FeedbackExtractionService(client=fake_client, max_corrective_retries=1)

        result = asyncio.run(service.extract_feedback("How much does the pro tier cost?"))

        self.assertFalse(result.is_valid)
        self.assertTrue(any("Missing required field: 'category'" in err for err in result.errors))

    def test_invalid_enum_value_failure(self) -> None:
        invalid_enum_json = (
            '{\n'
            '  "category": "outrage",\n'
            '  "sentiment": "furious",\n'
            '  "urgency": "catastrophic",\n'
            '  "summary": "User is very angry",\n'
            '  "confidence": 0.99\n'
            '}'
        )
        fake_client = FakeLlmClient([invalid_enum_json, invalid_enum_json])
        service = FeedbackExtractionService(client=fake_client, max_corrective_retries=1)

        result = asyncio.run(service.extract_feedback("Your service is completely broken!"))

        self.assertFalse(result.is_valid)
        self.assertTrue(any("Invalid 'category'" in err for err in result.errors))
        self.assertTrue(any("Invalid 'sentiment'" in err for err in result.errors))
        self.assertTrue(any("Invalid 'urgency'" in err for err in result.errors))

    def test_confidence_out_of_range_failure(self) -> None:
        invalid_confidence_json = (
            '{\n'
            '  "category": "billing",\n'
            '  "sentiment": "neutral",\n'
            '  "urgency": "medium",\n'
            '  "summary": "Double charge on invoice",\n'
            '  "confidence": 1.5\n'
            '}'
        )
        fake_client = FakeLlmClient([invalid_confidence_json, invalid_confidence_json])
        service = FeedbackExtractionService(client=fake_client, max_corrective_retries=1)

        result = asyncio.run(service.extract_feedback("I see two charges on my invoice."))

        self.assertFalse(result.is_valid)
        self.assertTrue(any("Field 'confidence' must be between 0.0 and 1.0" in err for err in result.errors))

    def test_corrective_retry_succeeds_on_second_attempt(self) -> None:
        invalid_first = '{"category": "bug", "summary": "App crashed"}'  # missing sentiment, urgency, confidence
        valid_second = (
            '{\n'
            '  "category": "bug",\n'
            '  "sentiment": "negative",\n'
            '  "urgency": "high",\n'
            '  "summary": "App crashed on launch",\n'
            '  "confidence": 0.92\n'
            '}'
        )
        fake_client = FakeLlmClient([invalid_first, valid_second])
        service = FeedbackExtractionService(client=fake_client, max_corrective_retries=1)

        result = asyncio.run(service.extract_feedback("App crashed on launch"))

        self.assertTrue(result.is_valid)
        self.assertEqual(fake_client.call_count, 2)
        # Verify that corrective prompt included previous error feedback
        corrective_request = fake_client.recorded_requests[1]
        self.assertIn("Your previous JSON output was invalid", corrective_request.prompt)

    def test_boolean_confidence_rejected(self) -> None:
        """Verify that boolean true/false in confidence field is rejected."""
        bool_confidence_json = (
            '{\n'
            '  "category": "bug",\n'
            '  "sentiment": "negative",\n'
            '  "urgency": "high",\n'
            '  "summary": "Crash on save",\n'
            '  "confidence": true\n'
            '}'
        )
        fake_client = FakeLlmClient([bool_confidence_json, bool_confidence_json])
        service = FeedbackExtractionService(client=fake_client, max_corrective_retries=0)

        result = asyncio.run(service.extract_feedback("Crash on save"))

        self.assertFalse(result.is_valid)
        self.assertTrue(any("Field 'confidence' must be a numeric float" in err for err in result.errors))

    def test_unexpected_fields_rejected(self) -> None:
        """Verify strict schema rejects unpermitted unexpected fields."""
        extra_fields_json = (
            '{\n'
            '  "category": "bug",\n'
            '  "sentiment": "negative",\n'
            '  "urgency": "medium",\n'
            '  "summary": "Export error",\n'
            '  "confidence": 0.95,\n'
            '  "admin_override": true,\n'
            '  "injected_field": "unauthorized"\n'
            '}'
        )
        fake_client = FakeLlmClient([extra_fields_json])
        service = FeedbackExtractionService(client=fake_client, max_corrective_retries=0)

        result = asyncio.run(service.extract_feedback("Export error"))

        self.assertFalse(result.is_valid)
        self.assertTrue(any("Unexpected fields not permitted in strict schema" in err for err in result.errors))
        self.assertTrue(any("admin_override" in err for err in result.errors))

    def test_valid_numeric_confidence_boundaries(self) -> None:
        """Verify confidence boundaries at 0.0, 0.5, and 1.0 pass validation."""
        for val in [0.0, 0.5, 1.0]:
            json_str = (
                f'{{\n'
                f'  "category": "inquiry",\n'
                f'  "sentiment": "neutral",\n'
                f'  "urgency": "low",\n'
                f'  "summary": "API limits query",\n'
                f'  "confidence": {val}\n'
                f'}}'
            )
            fake_client = FakeLlmClient([json_str])
            service = FeedbackExtractionService(client=fake_client)
            result = asyncio.run(service.extract_feedback("What are API limits?"))
            self.assertTrue(result.is_valid)
            self.assertEqual(result.unwrap().confidence, val)


if __name__ == "__main__":
    unittest.main()
