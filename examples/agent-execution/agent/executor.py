"""Bounded execution with identity-bound replay and fail-closed ambiguous outcomes."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import math
import time
from typing import Any, Mapping

from contracts.agent import CapabilityPort, ExecutionReceipt, SideEffectLevel
from contracts.telemetry import AiOperationContext
from ai_telemetry import traced
from .observation import bounded_json, exception_message


class ToolExecutor:
    """Process-local replay protection; durable external mutations need domain receipts."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self._idempotency_cache: dict[str, tuple[ExecutionReceipt, Any]] = {}
        self._identities: dict[str, str] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self.execution_history: list[ExecutionReceipt] = []

    @traced("tool.execute", "local")
    async def execute_tool(
        self,
        capability: CapabilityPort,
        arguments: Mapping[str, Any],
        action_id: str | None = None,
        context: AiOperationContext | None = None,
        execution_scope: str = "executor-local",
    ) -> tuple[ExecutionReceipt, Any]:
        preview, truncated = bounded_json(dict(arguments), 16384)
        if truncated:
            raise ValueError("Tool arguments exceed execution boundary budget")
        arguments = json.loads(preview)
        if not execution_scope.strip():
            raise ValueError("Execution scope must not be empty")
        key = action_id or str(arguments.get("action_id", f"act-{time.time_ns()}"))
        mutating = capability.metadata.side_effect_level == SideEffectLevel.STATE_MUTATING
        if mutating and not (action_id or arguments.get("action_id")):
            raise ValueError("Mutating operations require an action_id")
        if mutating and (not isinstance(key, str) or not key.strip()):
            raise ValueError("Mutating action_id must be a nonempty string")
        if action_id and arguments.get("action_id", action_id) != action_id:
            raise ValueError("Explicit action_id conflicts with argument action_id")
        identity = json.dumps(
            [execution_scope, id(capability), capability.metadata.name, dict(arguments)],
            sort_keys=True,
            allow_nan=False,
        )
        if mutating:
            if key in self._identities and self._identities[key] != identity:
                raise ValueError("Action ID reused with a different capability or arguments")
            if key not in self._identities and len(self._identities) >= 10000:
                raise ValueError("Executor action capacity exceeded; use durable execution")
            self._identities[key] = identity
            async with self._locks.setdefault(key, asyncio.Lock()):
                if key in self._idempotency_cache:
                    receipt, result = self._idempotency_cache[key]
                    return receipt, {"idempotent_replay": True, "cached_result": deepcopy(result)}
                return await self._execute(capability, arguments, key, context, mutating)
        return await self._execute(capability, arguments, key, context, mutating)

    async def _execute(
        self,
        capability: CapabilityPort,
        arguments: Mapping[str, Any],
        key: str,
        context: AiOperationContext | None,
        mutating: bool,
    ) -> tuple[ExecutionReceipt, Any]:
        started = time.time()
        status = "succeeded"
        error: str | None = None
        try:
            result = await asyncio.wait_for(
                capability.execute(arguments, context=context), self.timeout_seconds
            )
            if isinstance(result, dict) and (result.get("error") or result.get("success") is False):
                status, error = "failed", "Tool reported failure"
            preview, truncated = bounded_json(result, 16384)
            if truncated:
                # A mutation may already have happened. Never retry it as a known failure.
                status = "ambiguous" if mutating else "failed"
                error = "Tool result exceeds execution boundary budget"
                result = {"error": True, "message": error, "preview": preview}
            else:
                result = json.loads(preview)
        except asyncio.TimeoutError:
            status = "ambiguous" if mutating else "failed"
            error = "Operation timed out"
            result = {"error": True, "message": "Tool execution timed out; reconcile before retry"}
        except asyncio.CancelledError:
            if mutating:
                receipt = ExecutionReceipt(
                    key, capability.metadata.name, "ambiguous", error_message="Execution cancelled"
                )
                self._idempotency_cache[key] = (
                    receipt,
                    {"error": True, "message": "Reconciliation required"},
                )
                self.execution_history.append(receipt)
            raise
        except Exception as exc:
            status = "ambiguous" if mutating else "failed"
            error = exception_message(exc)
            result = {"error": True, "message": f"Tool execution failed: {error}"}
        receipt = ExecutionReceipt(
            key,
            capability.metadata.name,
            status,
            executed_at=started,
            result_summary=f"Executed {capability.metadata.name} ({status})",
            error_message=error,
        )
        if mutating:
            self._idempotency_cache[key] = (receipt, deepcopy(result))
        self.execution_history.append(receipt)
        return receipt, result
