"""Unit tests for ContextBuilder and evidence budgeting."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
RAG_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, RAG_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from rag.context_builder import EVIDENCE_FOOTER, EVIDENCE_HEADER, ContextBuilder
from rag.document import Chunk
from rag.retriever import RetrievalResult


class TestContextBuilder(unittest.TestCase):
    """Test suite verifying context formatting, delimiters, and budget limits."""

    def setUp(self) -> None:
        self.chunk1 = Chunk(chunk_id="doc1#c0", document_id="doc1", chunk_index=0, text="First evidence passage.")
        self.chunk2 = Chunk(chunk_id="doc2#c0", document_id="doc2", chunk_index=0, text="Second evidence passage.")
        self.chunk3 = Chunk(chunk_id="doc3#c0", document_id="doc3", chunk_index=0, text="Third evidence passage.")

    def test_empty_results_handling(self) -> None:
        builder = ContextBuilder()
        res = builder.build_context([])
        self.assertIn("[NO RELEVANT EVIDENCE FOUND]", res.formatted_context)
        self.assertEqual(res.chunks_count, 0)
        self.assertEqual(res.included_chunk_ids, [])

    def test_context_delimiters_and_source_tags(self) -> None:
        builder = ContextBuilder(max_chunks=2)
        results = [
            RetrievalResult(chunk=self.chunk1, score=0.9, rank=1),
            RetrievalResult(chunk=self.chunk2, score=0.8, rank=2),
        ]
        res = builder.build_context(results)

        self.assertTrue(res.formatted_context.startswith(EVIDENCE_HEADER))
        self.assertTrue(res.formatted_context.endswith(EVIDENCE_FOOTER))
        self.assertIn("[Source ID: doc1#c0]", res.formatted_context)
        self.assertIn("[Source ID: doc2#c0]", res.formatted_context)
        self.assertEqual(res.included_chunk_ids, ["doc1#c0", "doc2#c0"])
        self.assertEqual(res.chunks_count, 2)
        self.assertFalse(res.truncated)

    def test_max_chunks_budget(self) -> None:
        builder = ContextBuilder(max_chunks=2)
        results = [
            RetrievalResult(chunk=self.chunk1, score=0.9, rank=1),
            RetrievalResult(chunk=self.chunk2, score=0.8, rank=2),
            RetrievalResult(chunk=self.chunk3, score=0.7, rank=3),
        ]
        res = builder.build_context(results)
        self.assertEqual(res.chunks_count, 2)
        self.assertIn("doc1#c0", res.included_chunk_ids)
        self.assertIn("doc2#c0", res.included_chunk_ids)
        self.assertNotIn("doc3#c0", res.included_chunk_ids)

    def test_character_budget_truncation(self) -> None:
        # Small budget that fits only 1 chunk
        builder = ContextBuilder(max_chunks=5, max_chars=180)

        results = [
            RetrievalResult(chunk=self.chunk1, score=0.9, rank=1),
            RetrievalResult(chunk=self.chunk2, score=0.8, rank=2),
        ]
        res = builder.build_context(results)
        self.assertTrue(res.truncated)
        self.assertEqual(res.chunks_count, 1)
        self.assertEqual(res.included_chunk_ids, ["doc1#c0"])


if __name__ == "__main__":
    unittest.main()
