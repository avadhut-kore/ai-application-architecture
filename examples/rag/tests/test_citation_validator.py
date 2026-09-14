"""Unit tests for CitationValidator and spoofing prevention."""

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

from rag.citation_validator import CitationValidator
from rag.document import Chunk, Document


class TestCitationValidator(unittest.TestCase):
    """Test suite verifying citation verification, rejection of spoofed IDs, and deduplication."""

    def setUp(self) -> None:
        self.doc1 = Document(document_id="sec-01", title="Data Retention Policy", content="...", source_uri="sec-01.md")
        self.doc2 = Document(document_id="sec-02", title="Access Control Standard", content="...", source_uri="sec-02.md")
        self.validator = CitationValidator(document_catalog={"sec-01": self.doc1, "sec-02": self.doc2})

        self.retrieved_chunk1 = Chunk(chunk_id="sec-01#c0", document_id="sec-01", chunk_index=0, text="Audit logs kept 7 years")
        self.retrieved_chunk2 = Chunk(chunk_id="sec-02#c0", document_id="sec-02", chunk_index=0, text="Passwords 16 chars")

    def test_valid_citations_verification(self) -> None:
        res = self.validator.validate(
            cited_ids=["sec-01#c0", "sec-02#c0"],
            retrieved_chunks=[self.retrieved_chunk1, self.retrieved_chunk2],
        )
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.verified_citations), 2)
        self.assertEqual(res.rejected_citation_ids, [])

        cit0 = res.verified_citations[0]
        self.assertEqual(cit0.chunk_id, "sec-01#c0")
        self.assertEqual(cit0.document_id, "sec-01")
        self.assertEqual(cit0.source_title, "Data Retention Policy")
        self.assertEqual(cit0.source_uri, "sec-01.md")

    def test_spoofed_or_unretrieved_citation_rejected(self) -> None:
        # Model hallucinated "sec-99#c0" which was not retrieved
        res = self.validator.validate(
            cited_ids=["sec-01#c0", "sec-99#c0"],
            retrieved_chunks=[self.retrieved_chunk1],
        )
        self.assertFalse(res.is_valid)
        self.assertEqual(len(res.verified_citations), 1)
        self.assertEqual(res.rejected_citation_ids, ["sec-99#c0"])
        self.assertIn("sec-99#c0", res.errors[0])

    def test_deduplicate_citations(self) -> None:
        # Model cited the same chunk twice
        res = self.validator.validate(
            cited_ids=["sec-01#c0", "sec-01#c0"],
            retrieved_chunks=[self.retrieved_chunk1],
        )
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.verified_citations), 1)

    def test_insufficient_evidence_citations(self) -> None:
        res = self.validator.validate(
            cited_ids=[],
            retrieved_chunks=[],
            insufficient_evidence=True,
        )
        self.assertTrue(res.is_valid)
        self.assertTrue(res.has_insufficient_evidence)
        self.assertEqual(res.verified_citations, [])


if __name__ == "__main__":
    unittest.main()
