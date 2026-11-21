"""Negative controls for heading anchors and the documented Markdown rules."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("doc_validation", ROOT / "scripts/validate-docs.py")
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


class TestDocumentationValidation(unittest.TestCase):
    def test_missing_same_file_and_cross_file_anchors_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            one = root / "one.md"
            two = root / "two.md"
            one.write_text("# Title\n[bad](#missing)\n[bad](two.md#missing)\n", encoding="utf-8")
            two.write_text("# Present\n", encoding="utf-8")
            count, errors = docs.validate_internal_links([one, two], root)
            self.assertEqual(count, 2)
            self.assertEqual(len(errors), 2)

    def test_duplicate_heading_ids_and_structure_rules(self):
        anchors = docs.heading_anchors("# Title\n## Repeated\n## Repeated\n")
        self.assertIn("repeated-1", anchors)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "invalid.md"
            path.write_text("# One\n# Two\n```\ncontent\n```\n", encoding="utf-8")
            errors = docs.validate_markdown_structure([path], root)
            self.assertTrue(any("one H1" in error for error in errors))
            self.assertTrue(any("language tag" in error for error in errors))
