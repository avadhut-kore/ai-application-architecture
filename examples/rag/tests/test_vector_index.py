"""Unit tests for in-memory vector index and cosine similarity."""

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

from rag.document import Chunk
from rag.vector_index import InMemoryVectorIndex, VectorIndexPort, cosine_similarity


class TestVectorIndex(unittest.TestCase):
    """Test suite verifying vector index operations, cosine math, and metadata filtering."""

    def test_cosine_similarity_math(self) -> None:
        # Identical vectors -> 1.0
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        # Opposite vectors -> -1.0
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0)
        # Orthogonal vectors -> 0.0
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)
        # Zero-norm safe handling -> 0.0
        self.assertEqual(cosine_similarity([0.0, 0.0], [1.0, 2.0]), 0.0)
        self.assertEqual(cosine_similarity([0.0, 0.0], [0.0, 0.0]), 0.0)

    def test_cosine_similarity_dimension_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

    def test_vector_index_add_and_count(self) -> None:
        idx = InMemoryVectorIndex(dimensions=3)
        self.assertIsInstance(idx, VectorIndexPort)

        chunk1 = Chunk(chunk_id="c1", document_id="d1", chunk_index=0, text="First text")
        chunk2 = Chunk(chunk_id="c2", document_id="d1", chunk_index=1, text="Second text")

        idx.add(chunk1, [1.0, 0.0, 0.0])
        idx.add(chunk2, [0.0, 1.0, 0.0])
        self.assertEqual(idx.count(), 2)

        # Duplicate ID rejected
        with self.assertRaises(ValueError):
            idx.add(chunk1, [0.5, 0.5, 0.0])

        # Dimension mismatch rejected
        chunk3 = Chunk(chunk_id="c3", document_id="d2", chunk_index=0, text="Bad dim")
        with self.assertRaises(ValueError):
            idx.add(chunk3, [1.0, 0.0])

    def test_search_top_k_and_tie_breaking(self) -> None:
        idx = InMemoryVectorIndex(dimensions=2)
        chunk_a = Chunk(chunk_id="alpha", document_id="d1", chunk_index=0, text="Alpha")
        chunk_b = Chunk(chunk_id="beta", document_id="d1", chunk_index=1, text="Beta")
        chunk_c = Chunk(chunk_id="gamma", document_id="d1", chunk_index=2, text="Gamma")

        # chunk_a has higher similarity to [1.0, 0.0] than chunk_c
        # chunk_b and chunk_c both have [0.0, 1.0] vectors (identical score)
        idx.add(chunk_a, [1.0, 0.0])
        idx.add(chunk_c, [0.0, 1.0])
        idx.add(chunk_b, [0.0, 1.0])

        # Query pointing in [1.0, 0.1]
        results = idx.search([1.0, 0.1], top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk.chunk_id, "alpha")
        self.assertGreater(results[0].score, 0.9)

        # Query pointing along [0.0, 1.0] -> tie between beta and gamma
        # Deterministic tie-breaker sorts by chunk_id ascending: beta before gamma
        tie_results = idx.search([0.0, 1.0], top_k=2)
        self.assertEqual(tie_results[0].chunk.chunk_id, "beta")
        self.assertEqual(tie_results[1].chunk.chunk_id, "gamma")

    def test_search_metadata_filtering(self) -> None:
        idx = InMemoryVectorIndex(dimensions=2)
        c_sec = Chunk(
            chunk_id="sec-1",
            document_id="s1",
            chunk_index=0,
            text="Security text",
            metadata={"department": "security", "tier": "p1"},
        )
        c_hr = Chunk(
            chunk_id="hr-1",
            document_id="h1",
            chunk_index=0,
            text="HR text",
            metadata={"department": "hr", "tier": "p1"},
        )

        idx.add(c_sec, [1.0, 0.0])
        idx.add(c_hr, [1.0, 0.0])

        # Without filter, returns both
        all_res = idx.search([1.0, 0.0], top_k=5)
        self.assertEqual(len(all_res), 2)

        # With department: security filter, returns only c_sec
        sec_res = idx.search([1.0, 0.0], top_k=5, filters={"department": "security"})
        self.assertEqual(len(sec_res), 1)
        self.assertEqual(sec_res[0].chunk.chunk_id, "sec-1")

        # Non-matching filter returns empty
        empty_res = idx.search([1.0, 0.0], top_k=5, filters={"department": "finance"})
        self.assertEqual(len(empty_res), 0)


if __name__ == "__main__":
    unittest.main()
