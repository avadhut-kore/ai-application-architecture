"""Generic envelope for structured AI output parsing and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Optional, Sequence, TypeVar

from .errors import AiSchemaValidationError

T = TypeVar("T")


@dataclass(frozen=True)
class ValidationResult(Generic[T]):
    """Envelope wrapping structured AI output parsing results.

    Carries the strongly typed output if valid, or structured errors
    and original raw text if validation failed.
    """

    is_valid: bool
    data: Optional[T] = None
    raw_text: str = ""
    errors: Sequence[str] = field(default_factory=tuple)

    @classmethod
    def success(cls, data: T, raw_text: str = "") -> ValidationResult[T]:
        """Construct a successful validation result."""
        return cls(is_valid=True, data=data, raw_text=raw_text, errors=())

    @classmethod
    def failure(cls, errors: Sequence[str], raw_text: str = "") -> ValidationResult[T]:
        """Construct a failed validation result with error details."""
        return cls(is_valid=False, data=None, raw_text=raw_text, errors=tuple(errors))

    def unwrap(self) -> T:
        """Return the validated data or raise AiSchemaValidationError if invalid."""
        if not self.is_valid or self.data is None:
            raise AiSchemaValidationError(
                message=f"Validation failed with {len(self.errors)} error(s)",
                raw_output=self.raw_text,
                validation_errors=self.errors,
            )
        return self.data
