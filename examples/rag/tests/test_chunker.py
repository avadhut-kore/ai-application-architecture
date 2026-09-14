"""Unit tests for heading-aware chunking and document ingestion."""

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

from rag.chunker import HeadingAwareChunker
from rag.document import Document, make_chunk_id
from rag.ingestion import load_corpus_directory, normalize_text, parse_frontmatter


class TestChunkerAndIngestion(unittest.TestCase):
    """Test suite verifying document normalization and deterministic heading chunking."""

    def test_text_normalization(self) -> None:
        raw = "Line 1\r\nLine 2\r\r\n\n\n\nLine 3   "
        normalized = normalize_text(raw)
        self.assertNotIn("\r", normalized)
        self.assertNotIn("\n\n\n", normalized)
        self.assertTrue(normalized.endswith("Line 3"))

    def test_parse_frontmatter(self) -> None:
        raw = """---
id: test-doc
title: "Test Policy"
department: compliance
version: 1.5
enabled: true
---

# Test Policy Content
Body starts here.
"""
        meta, body = parse_frontmatter(raw)
        self.assertEqual(meta["id"], "test-doc")
        self.assertEqual(meta["title"], "Test Policy")
        self.assertEqual(meta["department"], "compliance")
        self.assertEqual(meta["version"], 1.5)
        self.assertIs(meta["enabled"], True)
        self.assertIn("Body starts here.", body)

    def test_chunker_empty_document(self) -> None:
        doc = Document(document_id="empty-doc", title="Empty", content="   ", source_uri="doc.md")
        chunker = HeadingAwareChunker()
        chunks = chunker.chunk_document(doc)
        self.assertEqual(chunks, [])

    def test_chunker_heading_split_and_metadata_propagation(self) -> None:
        content = """# Corporate Policy

## Section 1: Data Retention
Audit logs must be kept for 7 years in secure archive storage.

## Section 2: Access Control
All passwords must be at least 16 characters in length.
"""
        doc = Document(
            document_id="corp-01",
            title="Corporate Policy",
            content=content,
            source_uri="corp-01.md",
            metadata={"department": "compliance", "tier": "enterprise"},
        )

        chunker = HeadingAwareChunker(max_chunk_chars=500)
        chunks = chunker.chunk_document(doc)

        self.assertEqual(len(chunks), 2)
        # Check chunk 0
        self.assertEqual(chunks[0].chunk_id, "corp-01#c0")
        self.assertEqual(chunks[0].document_id, "corp-01")
        self.assertEqual(chunks[0].section_title, "Section 1: Data Retention")
        self.assertIn("7 years", chunks[0].text)
        self.assertEqual(chunks[0].metadata["department"], "compliance")

        # Check chunk 1
        self.assertEqual(chunks[1].chunk_id, "corp-01#c1")
        self.assertEqual(chunks[1].document_id, "corp-01")
        self.assertEqual(chunks[1].section_title, "Section 2: Access Control")
        self.assertIn("16 characters", chunks[1].text)
        self.assertEqual(chunks[1].metadata["tier"], "enterprise")

    def test_chunker_oversized_section_splitting(self) -> None:
        para1 = "Sentence one about topic A. " * 15
        para2 = "Sentence two about topic B. " * 15
        content = f"## Large Section\n\n{para1}\n\n{para2}"

        doc = Document(document_id="large-doc", title="Large Doc", content=content, source_uri="large.md")
        chunker = HeadingAwareChunker(max_chunk_chars=300)
        chunks = chunker.chunk_document(doc)

        self.assertGreaterEqual(len(chunks), 2)
        for c in chunks:
            self.assertEqual(c.document_id, "large-doc")
            self.assertTrue(c.chunk_id.startswith("large-doc#c"))
            self.assertLessEqual(len(c.text), 450)  # bounded size

    def test_load_corpus_directory(self) -> None:
        corpus_dir = RAG_DIR / "corpus"
        docs = load_corpus_directory(corpus_dir)
        self.assertGreaterEqual(len(docs), 7)
        doc_ids = [d.document_id for d in docs]
        self.assertIn("sec-01", doc_ids)
        self.assertIn("sec-02", doc_ids)
        self.assertIn("eng-01", doc_ids)
        self.assertIn("adversarial-01", doc_ids)


if __name__ == "__main__":
    unittest.main()
