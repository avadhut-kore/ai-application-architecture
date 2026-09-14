#!/usr/bin/env python3
"""Verification CLI for local Ollama embedding runtime availability and execution."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure building-blocks and adapter paths are in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
if str(BUILDING_BLOCKS_DIR) not in sys.path:
    sys.path.insert(0, str(BUILDING_BLOCKS_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from contracts.models import EmbeddingRequest
from ollama_embedding_adapter.adapter import OllamaEmbeddingAdapter

# Common local embedding model tags
KNOWN_EMBEDDING_MODELS = (
    "nomic-embed-text",
    "all-minilm",
    "bge-m3",
    "bge-small-en-v1.5",
    "mxbai-embed-large",
)


async def run_verification(endpoint: str, model: Optional[str] = None, allow_unverified: bool = False) -> int:
    print("=" * 60)
    print("ai-application-architecture — Ollama Embedding Verification")
    print("=" * 60)
    print(f"Target Endpoint: {endpoint}")

    adapter = OllamaEmbeddingAdapter(endpoint=endpoint, timeout_seconds=10.0)
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
        print("Resolution: Run `ollama pull nomic-embed-text` to install a local embedding model.")
        print("=" * 60)
        return 0 if allow_unverified else 1

    # Select target model
    target_model = model
    if not target_model:
        # Check if any installed model matches known embedding tags
        for m in installed_models:
            clean_m = m.split(":")[0]
            if any(known in clean_m for known in KNOWN_EMBEDDING_MODELS) or "embed" in clean_m:
                target_model = m
                break

    if not target_model:
        print("\nStatus: NOT VERIFIED")
        print(f"Reason: Installed models ({installed_models}) do not appear to include a dedicated embedding model.")
        print("Resolution: Run `ollama pull nomic-embed-text` to install the recommended local embedding model.")
        print("=" * 60)
        return 0 if allow_unverified else 1

    print(f"Executing Embedding Test using model: '{target_model}'...")

    request = EmbeddingRequest(
        inputs=["Enterprise AI Architecture and Knowledge Retrieval."],
        model=target_model,
    )

    try:
        response = await adapter.embed(request)
        print(f"\nModel: {response.model}")
        print(f"Dimensions: {response.dimensions}")
        print(f"Vectors Generated: {len(response.embeddings)}")
        print(f"Latency: {response.latency_ms:.1f}ms" if response.latency_ms else "Latency: N/A")
        if response.usage:
            print(f"Input Tokens: {response.usage.input_tokens}")
        print(f"Vector Sample (first 3 dims): {response.embeddings[0][:3]}")
        print("\nRESULT: PASS — Live Ollama embedding execution successfully verified.")
        print("=" * 60)
        return 0
    except Exception as ex:
        print(f"\nExecution Failed: {ex}")
        print("Status: FAIL")
        print("=" * 60)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify local Ollama embedding runtime execution.")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434"),
        help="Ollama API base URL",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_EMBED_MODEL"),
        help="Specific embedding model name to test",
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
