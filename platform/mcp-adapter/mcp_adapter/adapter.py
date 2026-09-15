"""Model Context Protocol (MCP) capability adapter conforming to CapabilityPort."""

from __future__ import annotations

import json
from typing import Any, List, Mapping, Optional, Sequence

from contracts.agent import (
    CapabilityMetadata,
    CapabilityPort,
    SideEffectLevel,
)
from contracts.telemetry import AiOperationContext

from .client import McpClient, McpClientError


class McpCapabilityAdapter(CapabilityPort):
    """Adapts an MCP-hosted tool into an application CapabilityPort with allowlisting enforcement."""

    def __init__(
        self,
        client: McpClient,
        tool_name: str,
        description: Optional[str] = None,
        input_schema: Optional[Mapping[str, Any]] = None,
        side_effect_level: SideEffectLevel = SideEffectLevel.READ_ONLY,
        requires_approval: bool = False,
        allowlist: Optional[Sequence[str]] = None,
    ) -> None:
        self.client = client
        self.tool_name = tool_name
        self.allowlist = set(allowlist) if allowlist is not None else None

        # 1. Enforce allowlisting boundary: reject unapproved tools
        if self.allowlist is not None and self.tool_name not in self.allowlist:
            raise ValueError(
                f"Security violation: MCP tool '{self.tool_name}' is not present in permitted allowlist {sorted(self.allowlist)}"
            )

        # 2. Derive metadata from server discovery if not explicitly supplied
        desc = description
        schema = input_schema

        if desc is None or schema is None:
            available_tools = self.client.list_tools()
            matching = [t for t in available_tools if t.get("name") == self.tool_name]
            if not matching:
                raise ValueError(f"Tool '{self.tool_name}' was not found on the connected MCP server")
            tool_spec = matching[0]
            desc = desc or tool_spec.get("description", f"MCP capability: {self.tool_name}")
            schema = schema or tool_spec.get("inputSchema", {"type": "object"})

        self._metadata = CapabilityMetadata(
            name=self.tool_name,
            description=desc,
            input_schema=schema,
            side_effect_level=side_effect_level,
            requires_approval=requires_approval,
        )

    @property
    def metadata(self) -> CapabilityMetadata:
        return self._metadata

    async def execute(
        self,
        arguments: Mapping[str, Any],
        context: Optional[AiOperationContext] = None,
    ) -> Any:
        """Invoke tool over MCP protocol transport and sanitize response content."""
        try:
            raw_response = self.client.call_tool(self.tool_name, arguments)
            is_error = raw_response.get("isError", False)
            content_items = raw_response.get("content", [])

            extracted_texts: List[str] = []
            for item in content_items:
                if isinstance(item, dict) and item.get("type") == "text":
                    extracted_texts.append(item.get("text", ""))

            full_text = "\n".join(extracted_texts).strip()

            # Attempt to decode JSON content if structured
            if full_text.startswith("{") or full_text.startswith("["):
                try:
                    parsed_payload = json.loads(full_text)
                    if is_error:
                        return {"error": True, "detail": parsed_payload}
                    return parsed_payload
                except json.JSONDecodeError:
                    pass

            if is_error:
                return {"error": True, "message": full_text or "MCP tool reported execution error"}

            return {"output": full_text}
        except McpClientError as err:
            return {"error": True, "message": f"MCP communication failure: {str(err)}"}
        except Exception as exc:
            return {"error": True, "message": f"Unexpected error executing MCP tool '{self.tool_name}': {str(exc)}"}


def create_mcp_capabilities(
    client: McpClient,
    allowlist: Sequence[str],
    mutating_tools: Optional[Sequence[str]] = None,
) -> Sequence[CapabilityPort]:
    """Discover all tools from an MCP server and wrap permitted tools in CapabilityPort instances."""
    client.initialize()
    allowed_set = set(allowlist)
    mutating_set = set(mutating_tools or [])
    available = client.list_tools()

    adapters: List[CapabilityPort] = []
    for tool_spec in available:
        name = tool_spec.get("name")
        if not name or name not in allowed_set:
            continue

        is_mutating = name in mutating_set
        side_effect = SideEffectLevel.STATE_MUTATING if is_mutating else SideEffectLevel.READ_ONLY
        adapter = McpCapabilityAdapter(
            client=client,
            tool_name=name,
            description=tool_spec.get("description"),
            input_schema=tool_spec.get("inputSchema"),
            side_effect_level=side_effect,
            requires_approval=is_mutating,
            allowlist=allowlist,
        )
        adapters.append(adapter)

    return adapters
