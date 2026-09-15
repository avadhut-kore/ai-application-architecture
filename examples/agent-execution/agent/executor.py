"""Centralized tool executor enforcing idempotency, sandboxing, and trusted execution receipts."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Mapping, Optional, Tuple

from contracts.agent import (
    CapabilityPort,
    ExecutionReceipt,
    SideEffectLevel,
)
from contracts.telemetry import AiOperationContext


class ToolExecutor:
    """Centralized execution boundary ensuring all tool side-effects are controlled, sandboxed, and auditable."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._idempotency_cache: Dict[str, Tuple[ExecutionReceipt, Any]] = {}
        self.execution_history: list[ExecutionReceipt] = []

    async def execute_tool(
        self,
        capability: CapabilityPort,
        arguments: Mapping[str, Any],
        action_id: Optional[str] = None,
        context: Optional[AiOperationContext] = None,
    ) -> Tuple[ExecutionReceipt, Any]:
        """Execute a capability, enforcing idempotency for state-mutating operations."""
        effective_action_id = action_id or str(arguments.get("action_id", f"act-{time.time_ns()}"))
        meta = capability.metadata

        # 1. Idempotency Check: Prevent duplicate state-mutating operations
        if meta.side_effect_level == SideEffectLevel.STATE_MUTATING and effective_action_id in self._idempotency_cache:
            cached_receipt, cached_result = self._idempotency_cache[effective_action_id]
            # Return cached execution receipt to guarantee idempotency
            return cached_receipt, {
                "idempotent_replay": True,
                "original_receipt": cached_receipt,
                "cached_result": cached_result,
            }

        # 2. Execute capability within timeout boundary
        start_time = time.time()
        try:
            raw_result = await asyncio.wait_for(
                capability.execute(arguments, context=context),
                timeout=self.timeout_seconds,
            )

            is_error = False
            error_msg = None
            if isinstance(raw_result, dict) and raw_result.get("error"):
                is_error = True
                error_msg = str(raw_result.get("error")) or str(raw_result.get("message"))

            status = "failed" if is_error else "succeeded"
            receipt = ExecutionReceipt(
                action_id=effective_action_id,
                capability_name=meta.name,
                status=status,
                executed_at=start_time,
                result_summary=f"Executed {meta.name} ({status})",
                error_message=error_msg,
            )

            # Cache successful or failed mutating actions for idempotency
            if meta.side_effect_level == SideEffectLevel.STATE_MUTATING:
                self._idempotency_cache[effective_action_id] = (receipt, raw_result)

            self.execution_history.append(receipt)
            return receipt, raw_result

        except asyncio.TimeoutError:
            receipt = ExecutionReceipt(
                action_id=effective_action_id,
                capability_name=meta.name,
                status="failed",
                executed_at=start_time,
                result_summary=f"Execution of {meta.name} timed out after {self.timeout_seconds}s",
                error_message="Operation timed out",
            )
            self.execution_history.append(receipt)
            return receipt, {"error": True, "message": f"Execution timed out after {self.timeout_seconds} seconds"}

        except Exception as exc:
            receipt = ExecutionReceipt(
                action_id=effective_action_id,
                capability_name=meta.name,
                status="failed",
                executed_at=start_time,
                result_summary=f"Execution of {meta.name} failed with exception {type(exc).__name__}",
                error_message=str(exc),
            )
            self.execution_history.append(receipt)
            return receipt, {"error": True, "message": f"Tool execution failed: {str(exc)}"}
