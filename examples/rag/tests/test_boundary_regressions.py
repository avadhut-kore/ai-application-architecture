"""Negative controls for schema, evidence identity and hard context budgets."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "building-blocks/python"), str(ROOT / "examples/rag")]

from rag.context_builder import ContextBuilder
from rag.document import Chunk, Document
from rag.chunker import HeadingAwareChunker
from rag.retriever import RetrievalResult
from rag.service import RAGService
from eval_runner import EvalScenario, evaluate_single_scenario


class FixedRetrieval:
    async def retrieve(self, **kwargs):
        return [
            RetrievalResult(Chunk(f"doc#c{i}", "doc", i, "Evidence " * 5), 0.9, i + 1)
            for i in range(2)
        ]


class FixedGeneration:
    def __init__(self, text):
        self.text = text

    async def generate(self, *args, **kwargs):
        return SimpleNamespace(text=self.text, model="test", latency_ms=0, usage=None)


class TestRagBoundaries(unittest.IsolatedAsyncioTestCase):
    async def test_duplicate_keys_and_partial_json_are_rejected(self):
        valid = '{"answer":"Claim","citations":["doc#c0"],"insufficient_evidence":false}'
        for text in [
            valid.replace('"answer":"Claim"', '"answer":"First","answer":"Claim"'),
            "prefix " + valid,
            valid + " suffix",
            "prefix ```json\n" + valid + "\n```",
        ]:
            result = await RAGService(FixedRetrieval(), FixedGeneration(text)).answer("q")
            self.assertFalse(result.schema_valid, text)
        result = await RAGService(
            FixedRetrieval(), FixedGeneration("```json\n" + valid + "\n```")
        ).answer("q")
        self.assertTrue(result.schema_valid)

    async def test_complete_prompt_budget_precedes_retrieval_and_generation(self):
        from unittest.mock import AsyncMock

        retrieval = FixedRetrieval()
        retrieval.retrieve = AsyncMock(side_effect=AssertionError("must not retrieve"))
        generation = FixedGeneration("")
        generation.generate = AsyncMock(side_effect=AssertionError("must not generate"))
        with self.assertRaises(ValueError):
            await RAGService(retrieval, generation).answer("q" * 20000)
        retrieval.retrieve.assert_not_awaited()
        generation.generate.assert_not_awaited()

    async def test_context_uses_only_remaining_complete_prompt_budget(self):
        from rag.service import SYSTEM_PROMPT

        captured = []

        class Capture(FixedGeneration):
            async def generate(self, request, **kwargs):
                captured.append(request)
                return await super().generate(request, **kwargs)

        service = RAGService(
            FixedRetrieval(),
            Capture('{"answer":"Claim","citations":["doc#c0"],"insufficient_evidence":false}'),
            max_request_chars=3000,
        )
        await service.answer("q")
        self.assertEqual(len(captured), 1)
        self.assertLessEqual(len(captured[0].prompt) + len(SYSTEM_PROMPT), 3000)
        for kwargs in [{"max_request_chars": 0}, {"max_output_tokens": 0}]:
            with self.assertRaises(ValueError):
                RAGService(FixedRetrieval(), FixedGeneration(""), **kwargs)
        with self.assertRaises(ValueError):
            ContextBuilder().build_context([], max_chars=-1)

    async def test_valid_citation_does_not_prove_an_unsupported_fact(self):
        response = await RAGService(
            FixedRetrieval(),
            FixedGeneration(
                '{"answer":"Invented fact", "citations":["doc#c0"], "insufficient_evidence":false}'
            ),
        ).answer("query")
        scenario = EvalScenario(
            "negative",
            "factual_single",
            "query",
            ["doc#c0"],
            ["doc"],
            ["Invented fact"],
            False,
            None,
            "Unsupported fact despite valid source ID",
        )
        self.assertTrue(response.citation_validation.is_valid)
        self.assertFalse(evaluate_single_scenario(scenario, response).grounded)

    async def test_excluded_chunk_cannot_be_verified(self):
        service = RAGService(
            FixedRetrieval(),
            FixedGeneration(
                '{"answer":"Claim", "citations":["doc#c1"], "insufficient_evidence":false}'
            ),
            context_builder=ContextBuilder(max_chunks=1),
        )
        result = await service.answer("query")
        self.assertEqual(result.context_build.included_chunk_ids, ["doc#c0"])
        self.assertFalse(result.citation_validation.is_valid)
        self.assertEqual(result.citations, [])

    async def test_wrong_types_and_extra_fields_fail_closed(self):
        for text in [
            '{"answer":123,"citations":[],"insufficient_evidence":false}',
            '{"answer":"a","citations":[],"insufficient_evidence":"false"}',
            '{"answer":"a","citations":[3],"insufficient_evidence":false}',
            '{"answer":"a","citations":[],"insufficient_evidence":true,"extra":1}',
            '{"answer":"a","citations":[],"insufficient_evidence":false}',
        ]:
            result = await RAGService(FixedRetrieval(), FixedGeneration(text)).answer("q")
            self.assertFalse(result.schema_valid, text)
            self.assertTrue(result.insufficient_evidence)
            self.assertEqual(result.citations, [])

    def test_context_never_exceeds_small_budget(self):
        result = ContextBuilder(max_chars=50).build_context(
            [RetrievalResult(Chunk("d#c0", "d", 0, "long evidence" * 100), 1, 1)]
        )
        self.assertLessEqual(result.total_chars, 50)
        self.assertEqual(result.included_chunk_ids, [])

    def test_single_oversized_paragraph_is_bounded(self):
        chunks = HeadingAwareChunker(max_chunk_chars=100, min_chunk_chars=10).chunk_document(
            Document("d", "Title", "# Section\n\n" + "x" * 1000, "local")
        )
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.text) <= 100 for chunk in chunks))
