#!/usr/bin/env python3
"""Verification CLI for local Ollama runtime availability and model execution."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ensure building-blocks and adapter paths are in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
if str(BUILDING_BLOCKS_DIR) not in sys.path:
    sys.path.insert(0, str(BUILDING_BLOCKS_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from contracts.models import CompletionRequest
from ollama_adapter.adapter import OllamaAdapter


async def run_verification(endpoint: str, model: Optional[str] = None, allow_unverified: bool = False) -> int:
    print("=" * 60)
    print("ai-application-architecture — Ollama Runtime Verification")
    print("=" * 60)
    print(f"Target Endpoint: {endpoint}")

    adapter = OllamaAdapter(endpoint=endpoint, timeout_seconds=10.0)
    is_healthy = await adapter.check_health()

    if not is_healthy:
        print("\nStatus: NOT VERIFIED")
        print(f"Reason: Ollama daemon is unreachable at '{endpoint}'.")
        print("Note: In offline CI environments, deterministic unit tests verify adapter behavior.")
        print("      To run live verification, start Ollama locally (`ollama serve`).")
        print("=" * 60)
        return 0 if allow_unverified else 1

    installed_models = await adapter.get_installed_models()
    print(f"Connection: Reachable (HTTP 200 OK)")
    print(f"Installed Models: {installed_models if installed_models else 'None'}")

    if not installed_models:
        print("\nStatus: NOT VERIFIED")
        print("Reason: Ollama daemon is running, but no models are installed.")
        print("Resolution: Run `ollama pull <model>` (e.g. `ollama pull llama3.2`) to install a model.")
        print("=" * 60)
        return 0 if allow_unverified else 1

    target_model = model or installed_models[0]
    print(f"Executing Generation Test using model: '{target_model}'...")

    request = CompletionRequest(
        prompt="Reply with the exact word 'PONG' and nothing else.",
        model=target_model,
        temperature=0.0,
        max_tokens=10,
    )

    try:
        response = await adapter.generate(request)
        print(f"\nModel Response: {response.text.strip()!r}")
        print(f"Latency: {response.latency_ms:.1f}ms" if response.latency_ms else "Latency: N/A")
        if response.usage:
            print(f"Tokens: prompt={response.usage.input_tokens}, completion={response.usage.output_tokens}")
        print(f"Finish Reason: {response.finish_reason.value}")
        print("\nRESULT: PASS — Live Ollama execution successfully verified.")
        print("=" * 60)
        return 0
    except Exception as ex:
        print(f"\nExecution Failed: {ex}")
        print("Status: FAIL")
        print("=" * 60)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify local Ollama runtime execution.")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434"),
        help="Ollama API base URL",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL"),
        help="Specific model name to test (defaults to first installed model)",
    )
    parser.add_argument(
        "--allow-unverified",
        action="store_true",
        help="Exit with code 0 instead of 1 when Ollama is unreachable or unverified",
    )
    args = parser.parse_args()

    return asyncio.run(
        run_verification(endpoint=args.endpoint, model=args.model, allow_unverified=args.allow_unverified)
    )


if __name__ == "__main__":
    sys.exit(main())
