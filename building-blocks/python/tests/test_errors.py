"""Unit tests for the bounded AiError taxonomy."""

import unittest

from contracts.errors import (
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


class TestErrors(unittest.TestCase):
    """Test suite verifying error hierarchy and classification."""

    def test_transient_errors_classification(self) -> None:
        rate_limit = AiRateLimitError(retry_after_seconds=5.0)
        self.assertIsInstance(rate_limit, AiTransientError)
        self.assertIsInstance(rate_limit, AiError)
        self.assertTrue(rate_limit.is_transient)
        self.assertEqual(rate_limit.error_code, "AI_RATE_LIMIT")
        self.assertEqual(rate_limit.retry_after_seconds, 5.0)
        self.assertEqual(rate_limit.details.get("retry_after_seconds"), 5.0)

        timeout = AiTimeoutError()
        self.assertIsInstance(timeout, AiTransientError)
        self.assertTrue(timeout.is_transient)
        self.assertEqual(timeout.error_code, "AI_TIMEOUT")

        unavailable = AiProviderUnavailableError()
        self.assertIsInstance(unavailable, AiTransientError)
        self.assertTrue(unavailable.is_transient)
        self.assertEqual(unavailable.error_code, "AI_PROVIDER_UNAVAILABLE")

    def test_non_transient_errors_classification(self) -> None:
        auth_err = AiAuthenticationError()
        self.assertIsInstance(auth_err, AiNonTransientError)
        self.assertIsInstance(auth_err, AiError)
        self.assertFalse(auth_err.is_transient)
        self.assertEqual(auth_err.error_code, "AI_AUTHENTICATION_ERROR")

        invalid_req = AiInvalidRequestError("Context window exceeded")
        self.assertIsInstance(invalid_req, AiNonTransientError)
        self.assertFalse(invalid_req.is_transient)
        self.assertEqual(invalid_req.error_code, "AI_INVALID_REQUEST")

        model_not_found = AiModelNotFoundError("mistral:7b")
        self.assertIsInstance(model_not_found, AiNonTransientError)
        self.assertFalse(model_not_found.is_transient)
        self.assertEqual(model_not_found.error_code, "AI_MODEL_NOT_FOUND")
        self.assertEqual(model_not_found.model_name, "mistral:7b")

    def test_semantic_errors_classification(self) -> None:
        schema_err = AiSchemaValidationError(
            "JSON parse error",
            raw_output="invalid json",
            validation_errors=["Expected key 'amount'"],
        )
        self.assertIsInstance(schema_err, AiSemanticError)
        self.assertIsInstance(schema_err, AiNonTransientError)
        self.assertFalse(schema_err.is_transient)
        self.assertEqual(schema_err.error_code, "AI_SCHEMA_VALIDATION_ERROR")
        self.assertEqual(schema_err.raw_output, "invalid json")
        self.assertEqual(schema_err.validation_errors, ["Expected key 'amount'"])

        content_filter = AiContentFilterError()
        self.assertIsInstance(content_filter, AiSemanticError)
        self.assertFalse(content_filter.is_transient)
        self.assertEqual(content_filter.error_code, "AI_CONTENT_FILTER_ERROR")


if __name__ == "__main__":
    unittest.main()
