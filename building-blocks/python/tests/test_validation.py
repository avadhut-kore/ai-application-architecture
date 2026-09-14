"""Unit tests for the ValidationResult structured parsing envelope."""

import unittest
from dataclasses import dataclass

from contracts.errors import AiSchemaValidationError
from contracts.validation import ValidationResult


@dataclass(frozen=True)
class SamplePayload:
    query: str
    confidence: float


class TestValidation(unittest.TestCase):
    """Test suite verifying ValidationResult behavior and unwrap semantics."""

    def test_validation_success(self) -> None:
        payload = SamplePayload(query="search term", confidence=0.95)
        res = ValidationResult.success(payload, raw_text='{"query": "search term", "confidence": 0.95}')

        self.assertTrue(res.is_valid)
        self.assertEqual(res.raw_text, '{"query": "search term", "confidence": 0.95}')
        self.assertEqual(len(res.errors), 0)
        self.assertEqual(res.unwrap(), payload)

    def test_validation_failure(self) -> None:
        errors = ["Missing required field: confidence", "Invalid field: query"]
        res = ValidationResult[SamplePayload].failure(
            errors=errors, raw_text='{"unknown": "data"}'
        )

        self.assertFalse(res.is_valid)
        self.assertIsNone(res.data)
        self.assertEqual(res.raw_text, '{"unknown": "data"}')
        self.assertEqual(res.errors, tuple(errors))

        with self.assertRaises(AiSchemaValidationError) as ctx:
            res.unwrap()

        exc = ctx.exception
        self.assertEqual(exc.raw_output, '{"unknown": "data"}')
        self.assertEqual(exc.validation_errors, errors)
        self.assertEqual(exc.error_code, "AI_SCHEMA_VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()
