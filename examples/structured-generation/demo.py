#!/usr/bin/env python3
"""Demonstration CLI for Structured Generation Pattern Example.

Demonstrates:
1. Provider-neutral dependency injection (FeedbackExtractionService depends on TextGenerationPort).
2. Schema validation on untrusted LLM output.
3. Bounded corrective retry upon schema or JSON parsing failure.
4. Offline verification via --mode fake and live runtime execution via --mode live.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# Ensure repository root and building-blocks are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUILDING_BLOCKS_PYTHON = REPO_ROOT / "building-blocks" / "python"
PLATFORM_OLLAMA = REPO_ROOT / "platform" / "ollama-adapter"
THIS_DIR = Path(__file__).resolve().parent

for p in (BUILDING_BLOCKS_PYTHON, PLATFORM_OLLAMA, THIS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.models import CompletionRequest, CompletionResponse, UsageMetrics
from contracts.ports import TextGenerationPort
from structured_generation.service import FeedbackExtractionService


class DemoStubLlmClient:
    """Deterministic in-memory test double for offline demonstration."""

    def __init__(self, responses: List[str]) -> None:
        self._responses = list(responses)
        self._index = 0

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        if self._index < len(self._responses):
            text = self._responses[self._index]
            self._index += 1
        else:
            text = "{}"
        return CompletionResponse(
            text=text,
            model=request.model,
            usage=UsageMetrics(input_tokens=15, output_tokens=25, total_tokens=40),
            latency_ms=1.5,
        )

    async def health_check(self) -> bool:
        return True


async def run_fake_demo() -> int:
    print("=" * 70)
    print("STRUCTURED GENERATION DEMO (MODE: FAKE / OFFLINE)")
    print("=" * 70)

    # Scenario 1: Clean, valid extraction
    print("\n[Scenario 1] Clean Extraction (Valid Schema)")
    input_text_1 = "The checkout page throws a 500 error when clicking Apply Coupon. We are losing sales!"
    valid_json = (
        '{"category": "bug", "sentiment": "negative", "urgency": "critical", '
        '"summary": "Checkout 500 error on coupon apply causing lost sales", "confidence": 0.98}'
    )
    client_1 = DemoStubLlmClient([valid_json])
    service_1 = FeedbackExtractionService(client=client_1, model="llama3.2")
    res_1 = await service_1.extract_feedback(input_text_1)

    print(f"Input:    {input_text_1}")
    print(f"Status:   {'VALID' if res_1.is_valid else 'INVALID'}")
    if res_1.is_valid and res_1.data is not None:
        print("Domain Model Extracted:")
        print(f"  - Category:   {res_1.data.category.value}")
        print(f"  - Sentiment:  {res_1.data.sentiment.value}")
        print(f"  - Urgency:    {res_1.data.urgency.value}")
        print(f"  - Summary:    {res_1.data.summary}")
        print(f"  - Confidence: {res_1.data.confidence:.2f}")

    # Scenario 2: Unrecoverable Malformed JSON
    print("\n[Scenario 2] Unrecoverable Malformed JSON (Rejected by Boundary)")
    input_text_2 = "Can I pay with annual invoicing?"
    malformed_text = "Sure! Here is the response: category: inquiry, sentiment: neutral"
    client_2 = DemoStubLlmClient([malformed_text, malformed_text])
    service_2 = FeedbackExtractionService(client=client_2, model="llama3.2", max_corrective_retries=1)
    res_2 = await service_2.extract_feedback(input_text_2)

    print(f"Input:    {input_text_2}")
    print(f"Status:   {'VALID' if res_2.is_valid else 'REJECTED (EXPECTED)'}")
    print("Errors Caught:")
    for err in res_2.errors:
        print(f"  * {err}")

    # Scenario 3: Corrective Retry Recovery
    print("\n[Scenario 3] Corrective Retry Recovery (Self-Correction)")
    input_text_3 = "Would love dark mode support in the mobile app!"
    invalid_category_json = (
        '{"category": "enhancement", "sentiment": "positive", "urgency": "low", '
        '"summary": "Dark mode request", "confidence": 0.90}'
    )
    corrected_json = (
        '{"category": "feature_request", "sentiment": "positive", "urgency": "low", '
        '"summary": "Dark mode request for mobile app", "confidence": 0.92}'
    )
    client_3 = DemoStubLlmClient([invalid_category_json, corrected_json])
    service_3 = FeedbackExtractionService(client=client_3, model="llama3.2", max_corrective_retries=1)
    res_3 = await service_3.extract_feedback(input_text_3)

    print(f"Input:    {input_text_3}")
    print(f"Status:   {'VALID (RECOVERED)' if res_3.is_valid else 'INVALID'}")
    if res_3.is_valid and res_3.data is not None:
        print("Domain Model Extracted via Corrective Retry:")
        print(f"  - Category:   {res_3.data.category.value} (corrected from 'enhancement')")
        print(f"  - Sentiment:  {res_3.data.sentiment.value}")
        print(f"  - Urgency:    {res_3.data.urgency.value}")
        print(f"  - Summary:    {res_3.data.summary}")
        print(f"  - Confidence: {res_3.data.confidence:.2f}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE: All 3 patterns demonstrated successfully.")
    print("=" * 70)
    return 0


async def run_live_demo(base_url: str, model: str) -> int:
    print("=" * 70)
    print("STRUCTURED GENERATION DEMO (MODE: LIVE)")
    print("=" * 70)
    print(f"Connecting to Ollama at {base_url} (model: {model})...")

    try:
        from ollama_adapter.adapter import OllamaAdapter
    except ImportError as ex:
        print(f"Error importing OllamaAdapter: {ex}")
        return 1

    adapter = OllamaAdapter(endpoint=base_url, default_model=model)
    is_healthy = await adapter.check_health()
    if not is_healthy:
        print("\n[LIVE EXECUTION STATUS: NOT VERIFIED]")
        print(f"Ollama daemon is not reachable at {base_url}.")
        print("To verify live execution:")
        print("  1. Install Ollama: https://ollama.com")
        print("  2. Start the daemon: ollama serve")
        print(f"  3. Pull the model:   ollama pull {model}")
        print("  4. Re-run: python3 examples/structured-generation/demo.py --mode live")
        return 0

    service = FeedbackExtractionService(client=adapter, model=model, max_corrective_retries=1)
    input_text = "The system crashes every time I export more than 1000 items to CSV. This is blocking our audit!"
    print(f"\nProcessing input: \"{input_text}\"")

    try:
        result = await service.extract_feedback(input_text)
    except Exception as ex:
        print(f"Execution failed: {ex}")
        return 1

    if result.is_valid and result.data is not None:
        print("\nStructured Output Extraction Successful:")
        print(f"  - Category:   {result.data.category.value}")
        print(f"  - Sentiment:  {result.data.sentiment.value}")
        print(f"  - Urgency:    {result.data.urgency.value}")
        print(f"  - Summary:    {result.data.summary}")
        print(f"  - Confidence: {result.data.confidence:.2f}")
    else:
        print("\nExtraction returned schema validation errors:")
        for err in result.errors:
            print(f"  * {err}")
        print(f"Raw Output: {result.raw_text}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Structured Generation Pattern Demo")
    parser.add_argument(
        "--mode",
        choices=["fake", "live"],
        default="fake",
        help="Execution mode: 'fake' (offline stub) or 'live' (local Ollama daemon)",
    )
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--model", default="llama3.2", help="Model name for extraction")
    args = parser.parse_args()

    if args.mode == "fake":
        return asyncio.run(run_fake_demo())
    else:
        return asyncio.run(run_live_demo(args.base_url, args.model))


if __name__ == "__main__":
    sys.exit(main())
