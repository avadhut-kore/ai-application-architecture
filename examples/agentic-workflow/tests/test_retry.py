"""Hermetic unit tests for StepRetryPolicy and mutation non-amplification invariants."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = REPO_ROOT / "examples" / "agent-execution"
WORKFLOW_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR, WORKFLOW_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from workflow.retry import StepRetryPolicy


class TestStepRetryPolicy(unittest.TestCase):
    """Verify retry bounds, exponential backoff, and state-mutation refusal."""

    def setUp(self) -> None:
        self.policy = StepRetryPolicy(max_retries=3, base_delay_ms=100.0, backoff_factor=2.0)

    def test_state_mutating_steps_never_retried(self) -> None:
        """CRITICAL INVARIANT: State-mutating steps return False regardless of exception or attempt."""
        exc = ConnectionError("Network timeout during credit transaction")
        # Attempt 0, 1, 2 must all return False when is_state_mutating is True
        self.assertFalse(self.policy.is_retryable(exc, attempt=0, is_state_mutating=True))
        self.assertFalse(self.policy.is_retryable(exc, attempt=1, is_state_mutating=True))
        self.assertFalse(self.policy.is_retryable(exc, attempt=2, is_state_mutating=True))

    def test_read_only_steps_retried_up_to_max(self) -> None:
        """Read-only steps return True for attempts < max_retries."""
        exc = TimeoutError("Transient database read failure")
        self.assertTrue(self.policy.is_retryable(exc, attempt=0, is_state_mutating=False))
        self.assertTrue(self.policy.is_retryable(exc, attempt=1, is_state_mutating=False))
        self.assertTrue(self.policy.is_retryable(exc, attempt=2, is_state_mutating=False))
        # Exceeds max_retries (3)
        self.assertFalse(self.policy.is_retryable(exc, attempt=3, is_state_mutating=False))
        self.assertFalse(self.policy.is_retryable(exc, attempt=4, is_state_mutating=False))

    def test_exponential_backoff_computation(self) -> None:
        """Delay scales exponentially: base * (factor ^ (attempt - 1))."""
        # base_delay_ms = 100ms -> 0.1s
        delay_0 = self.policy.compute_delay_seconds(0)
        delay_1 = self.policy.compute_delay_seconds(1)
        delay_2 = self.policy.compute_delay_seconds(2)
        delay_3 = self.policy.compute_delay_seconds(3)

        self.assertAlmostEqual(delay_0, 0.1)
        self.assertAlmostEqual(delay_1, 0.1)
        self.assertAlmostEqual(delay_2, 0.2)
        self.assertAlmostEqual(delay_3, 0.4)


if __name__ == "__main__":
    unittest.main()
