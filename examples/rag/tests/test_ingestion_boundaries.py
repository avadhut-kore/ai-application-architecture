"""Reject corrupt documents and normalize supported frontmatter deterministically."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "building-blocks/python"), str(ROOT / "examples/rag")]
from rag.document import Document, Chunk
from rag.ingestion import load_markdown_document, load_corpus_directory, parse_frontmatter


class TestIngestionBoundaries(unittest.TestCase):
    def test_invalid_entities_are_rejected(self):
        for args in [("", "t", "text", "uri"), ("d", "t", 1, "uri")]:
            with self.assertRaises(ValueError):
                Document(*args)
        for args in [
            ("", "d", 0, "text"),
            ("c", "", 0, "text"),
            ("c", "d", -1, "text"),
            ("c", "d", 0, ""),
        ]:
            with self.assertRaises(ValueError):
                Chunk(*args)

    def test_missing_files_and_frontmatter_types(self):
        metadata, text = parse_frontmatter(
            '---\n# ignored\nflag: false\nratio: 1.5\nlabel: "Quoted"\n---\n# Title\nbody'
        )
        self.assertIs(metadata["flag"], False)
        self.assertEqual(metadata["ratio"], 1.5)
        self.assertEqual(metadata["label"], "Quoted")
        self.assertIn("Title", text)
        self.assertEqual(parse_frontmatter("plain"), ({}, "plain"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FileNotFoundError):
                load_markdown_document(root / "missing.md")
            with self.assertRaises(NotADirectoryError):
                load_corpus_directory(root / "missing")
            (root / "doc.md").write_text("# Derived title\nBody", encoding="utf-8")
            (root / "_ignored.md").write_text("ignored", encoding="utf-8")
            documents = load_corpus_directory(root)
            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0].title, "Derived title")
