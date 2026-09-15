"""Bounded step retry policy preventing mutation amplification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple, Type


@dataclass(frozen=True)
class StepRetryPolicy:
    """Configurable step-level retry policy enforcing non-amplification invariants."""

    max_retries: int = 2
    base_delay_ms: float = 50.0
    backoff_factor: float = 2.0
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)

    def is_retryable(
        self,
        exc: Exception,
        attempt: int,
        is_state_mutating: bool = False,
    ) -> bool:
        """Determine if a failed step execution may be retried.

        CRITICAL SAFETY INVARIANT: State-mutating steps are NEVER blindly retried
        by the workflow engine without prior domain-state and receipt reconciliation.
        """
        if is_state_mutating:
            return False

        if attempt >= self.max_retries:
            return False

        return isinstance(exc, self.retryable_exceptions)

    def compute_delay_seconds(self, attempt: int) -> float:
        """Calculate exponential backoff delay in seconds."""
        exponent = max(0, attempt - 1)
        return (self.base_delay_ms / 1000.0) * (self.backoff_factor ** exponent)
