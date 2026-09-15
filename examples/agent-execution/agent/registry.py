"""Application-controlled capability registry and argument schema validation."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from contracts.agent import CapabilityMetadata, CapabilityPort
from contracts.validation import ValidationResult


class CapabilityRegistry:
    """Application-controlled registry enforcing tool allowlisting and parameter validation.

    Protects against arbitrary code execution by ensuring the model may only select
    from explicitly registered, approved capabilities.
    """

    def __init__(self, capabilities: Optional[Sequence[CapabilityPort]] = None) -> None:
        self._capabilities: Dict[str, CapabilityPort] = {}
        if capabilities:
            for cap in capabilities:
                self.register(cap)

    def register(self, capability: CapabilityPort) -> None:
        """Register an application capability. Rejects duplicate identifiers."""
        name = capability.metadata.name
        if name in self._capabilities:
            raise ValueError(f"Capability '{name}' is already registered in registry")
        self._capabilities[name] = capability

    def is_registered(self, name: str) -> bool:
        """Check if capability identifier exists in allowlisted registry."""
        return name in self._capabilities

    def get(self, name: str) -> Optional[CapabilityPort]:
        """Resolve capability by name."""
        return self._capabilities.get(name)

    def list_capabilities(self) -> Sequence[CapabilityMetadata]:
        """List all capability metadata registered in the application."""
        return [cap.metadata for cap in self._capabilities.values()]

    def get_tool_definitions_prompt(self) -> str:
        """Generate human-readable, model-facing capability specifications for reasoning context."""
        lines: List[str] = []
        for meta in self.list_capabilities():
            lines.append(f"• Tool: {meta.name}")
            lines.append(f"  Description: {meta.description}")
            lines.append(f"  Side Effect: {meta.side_effect_level.value.upper()}")
            lines.append(f"  Approval Required: {meta.requires_approval}")
            lines.append(f"  Required Arguments: {meta.input_schema.get('required', [])}")
            lines.append(f"  Parameters Schema: {meta.input_schema.get('properties', {})}")
            lines.append("")
        return "\n".join(lines).strip()

    def validate_arguments(self, capability_name: str, arguments: Mapping[str, Any]) -> ValidationResult:
        """Perform strict deterministic schema validation on model-proposed capability arguments.

        Validates required parameter presence, data types, and prohibits unknown fields.
        """
        capability = self.get(capability_name)
        if not capability:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown capability '{capability_name}'. Tool is not present in registered allowlist."],
            )

        schema = capability.metadata.input_schema
        errors: List[str] = []

        # 1. Check required properties
        required_fields = schema.get("required", [])
        for field_name in required_fields:
            if field_name not in arguments:
                errors.append(f"Missing required parameter '{field_name}' for capability '{capability_name}'")

        # 2. Check property types
        properties: Mapping[str, Any] = schema.get("properties", {})
        for prop_name, prop_val in arguments.items():
            if prop_name not in properties:
                if schema.get("additionalProperties") is False:
                    errors.append(f"Unexpected parameter '{prop_name}' is not allowed for capability '{capability_name}'")
                continue

            expected_type = properties[prop_name].get("type")
            if expected_type == "string" and not isinstance(prop_val, str):
                errors.append(f"Parameter '{prop_name}' must be a string, got {type(prop_val).__name__}")
            elif expected_type == "integer" and (not isinstance(prop_val, int) or isinstance(prop_val, bool)):
                errors.append(f"Parameter '{prop_name}' must be an integer, got {type(prop_val).__name__}")
            elif expected_type == "number" and not isinstance(prop_val, (int, float)):
                errors.append(f"Parameter '{prop_name}' must be a number, got {type(prop_val).__name__}")
            elif expected_type == "boolean" and not isinstance(prop_val, bool):
                errors.append(f"Parameter '{prop_name}' must be a boolean, got {type(prop_val).__name__}")
            elif expected_type == "array" and not isinstance(prop_val, (list, tuple)):
                errors.append(f"Parameter '{prop_name}' must be a list, got {type(prop_val).__name__}")
            elif expected_type == "object" and not isinstance(prop_val, dict):
                errors.append(f"Parameter '{prop_name}' must be an object, got {type(prop_val).__name__}")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
