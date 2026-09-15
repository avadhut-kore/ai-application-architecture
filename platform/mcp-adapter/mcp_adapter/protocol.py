"""JSON-RPC 2.0 protocol specifications and serialization for Model Context Protocol (MCP)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union


class JsonRpcErrorCode:
    """Standard JSON-RPC 2.0 error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


@dataclass(frozen=True)
class JsonRpcError:
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Mapping[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            payload["data"] = self.data
        return payload


@dataclass(frozen=True)
class JsonRpcRequest:
    """JSON-RPC 2.0 request payload."""

    method: str
    id: Union[str, int]
    params: Optional[Mapping[str, Any]] = None
    jsonrpc: str = "2.0"

    def to_dict(self) -> Mapping[str, Any]:
        payload: dict[str, Any] = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
        }
        if self.params is not None:
            payload["params"] = dict(self.params)
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> JsonRpcRequest:
        if data.get("jsonrpc") != "2.0":
            raise ValueError(f"Invalid JSON-RPC version: {data.get('jsonrpc')}")
        if "method" not in data or not isinstance(data["method"], str):
            raise ValueError("Missing or invalid 'method' field in JSON-RPC request")
        if "id" not in data:
            raise ValueError("Missing 'id' field in JSON-RPC request")
        return cls(
            method=data["method"],
            id=data["id"],
            params=data.get("params"),
        )


@dataclass(frozen=True)
class JsonRpcResponse:
    """JSON-RPC 2.0 response payload."""

    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None
    jsonrpc: str = "2.0"

    def to_dict(self) -> Mapping[str, Any]:
        payload: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            payload["error"] = self.error.to_dict()
        else:
            payload["result"] = self.result
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> JsonRpcResponse:
        if data.get("jsonrpc") != "2.0":
            raise ValueError(f"Invalid JSON-RPC version: {data.get('jsonrpc')}")
        if "id" not in data:
            raise ValueError("Missing 'id' field in JSON-RPC response")

        err: Optional[JsonRpcError] = None
        if "error" in data and isinstance(data["error"], dict):
            err_dict = data["error"]
            err = JsonRpcError(
                code=err_dict.get("code", JsonRpcErrorCode.INTERNAL_ERROR),
                message=err_dict.get("message", "Unknown error"),
                data=err_dict.get("data"),
            )

        return cls(
            id=data["id"],
            result=data.get("result"),
            error=err,
        )
