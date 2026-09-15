"""Client communicating with Model Context Protocol (MCP) servers over stdio or in-memory transport."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Mapping, Optional, Sequence

from .protocol import (
    JsonRpcError,
    JsonRpcRequest,
    JsonRpcResponse,
)
from .server import McpServer


class McpClientError(Exception):
    """Base exception for MCP client communication errors."""


class McpClient:
    """Client for Model Context Protocol servers operating via stdio or in-memory dispatch."""

    def __init__(
        self,
        server_instance: Optional[McpServer] = None,
        command: Optional[Sequence[str]] = None,
    ) -> None:
        self._server_instance = server_instance
        self._command = command
        self._process: Optional[subprocess.Popen[str]] = None
        self._next_id = 1

        if not self._server_instance and not self._command:
            raise ValueError("McpClient requires either server_instance or command")

        if self._command and not self._server_instance:
            self._start_process()

    def _start_process(self) -> None:
        """Start background subprocess for stdio transport."""
        assert self._command is not None
        import os
        from pathlib import Path
        env = os.environ.copy()
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        contracts_dir = str(root_dir / "building-blocks" / "python")
        adapter_dir = str(Path(__file__).resolve().parent.parent)
        curr_pypath = env.get("PYTHONPATH", "")
        prefix = f"{contracts_dir}:{adapter_dir}"
        env["PYTHONPATH"] = f"{prefix}:{curr_pypath}" if curr_pypath else prefix

        self._process = subprocess.Popen(
            list(self._command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )

    def _send_request(self, method: str, params: Optional[Mapping[str, Any]] = None) -> JsonRpcResponse:
        """Send a JSON-RPC 2.0 request and parse the response."""
        req_id = self._next_id
        self._next_id += 1
        req = JsonRpcRequest(method=method, id=req_id, params=params)

        if self._server_instance:
            # Direct in-memory dispatch
            return self._server_instance.handle_request(req)

        if not self._process or not self._process.stdin or not self._process.stdout:
            raise McpClientError("MCP server process is not running")

        try:
            line_out = req.to_json() + "\n"
            self._process.stdin.write(line_out)
            self._process.stdin.flush()

            line_in = self._process.stdout.readline()
            if not line_in:
                raise McpClientError("MCP server process closed stream without responding")

            data = json.loads(line_in.strip())
            return JsonRpcResponse.from_dict(data)
        except Exception as exc:
            raise McpClientError(f"Failed to communicate with MCP server: {exc}") from exc

    def initialize(self) -> Mapping[str, Any]:
        """Perform MCP protocol handshake."""
        resp = self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "ai-architecture-mcp-client", "version": "1.0.0"},
            },
        )
        if resp.error:
            raise McpClientError(f"Initialization error: {resp.error.message}")
        return dict(resp.result or {})

    def list_tools(self) -> Sequence[Mapping[str, Any]]:
        """Query server for list of available capabilities."""
        resp = self._send_request("tools/list")
        if resp.error:
            raise McpClientError(f"tools/list error: {resp.error.message}")
        result = resp.result or {}
        return list(result.get("tools", []))

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        """Invoke a tool on the MCP server."""
        resp = self._send_request("tools/call", {"name": name, "arguments": dict(arguments)})
        if resp.error:
            raise McpClientError(f"tools/call error ({resp.error.code}): {resp.error.message}")
        result = resp.result or {}
        return dict(result)

    def close(self) -> None:
        """Terminate connection and clean up resources."""
        if self._process:
            try:
                # Terminate child process first so kernel signals EOF to any blocked readline()
                self._process.terminate()
                try:
                    self._process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=0.5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass

            for pipe in (self._process.stdin, self._process.stdout, self._process.stderr):
                if pipe:
                    try:
                        pipe.close()
                    except Exception:
                        pass
            self._process = None
