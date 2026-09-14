"""Unit tests for Phase 3 Reference Artifact Templates and Manifest Validation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure repo root and scripts are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from artifact_validator import (  # noqa: E402
    find_all_artifacts,
    validate_all_templates,
    validate_artifact,
    validate_manifest,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestTemplatesAndManifests(unittest.TestCase):
    """Test suite verifying template manifests, tier structures, and rejection cases."""

    def test_canonical_templates_pass_validation(self) -> None:
        templates_root = REPO_ROOT / "templates"
        ok, errors = validate_all_templates(templates_root)
        self.assertTrue(ok, f"Canonical templates failed validation: {errors}")
        self.assertEqual(len(errors), 0)

    def test_valid_tier1_fixture(self) -> None:
        fixture_dir = FIXTURES_DIR / "valid_tier1"
        ok, errors = validate_artifact(fixture_dir)
        self.assertTrue(ok, f"Valid Tier 1 fixture failed: {errors}")
        self.assertEqual(len(errors), 0)

    def test_valid_tier2_fixture(self) -> None:
        fixture_dir = FIXTURES_DIR / "valid_tier2"
        ok, errors = validate_artifact(fixture_dir)
        self.assertTrue(ok, f"Valid Tier 2 fixture failed: {errors}")
        self.assertEqual(len(errors), 0)

    def test_valid_tier3_fixture(self) -> None:
        fixture_dir = FIXTURES_DIR / "valid_tier3"
        ok, errors = validate_artifact(fixture_dir)
        self.assertTrue(ok, f"Valid Tier 3 fixture failed: {errors}")
        self.assertEqual(len(errors), 0)

    def test_valid_tier4_fixture(self) -> None:
        fixture_dir = FIXTURES_DIR / "valid_tier4"
        ok, errors = validate_artifact(fixture_dir)
        self.assertTrue(ok, f"Valid Tier 4 fixture failed: {errors}")
        self.assertEqual(len(errors), 0)

    def test_invalid_tier_number_rejected(self) -> None:
        fixture_dir = FIXTURES_DIR / "invalid_tier_number"
        ok, errors = validate_artifact(fixture_dir)
        self.assertFalse(ok)
        self.assertTrue(any("Invalid 'tier'" in err for err in errors))

    def test_missing_tier1_docs_rejected(self) -> None:
        fixture_dir = FIXTURES_DIR / "invalid_missing_docs"
        ok, errors = validate_artifact(fixture_dir)
        self.assertFalse(ok)
        self.assertTrue(any("Tier 1 artifact missing required file: docs/requirements.md" in err for err in errors))
        self.assertTrue(any("Tier 1 artifact missing required file: docs/architecture.md" in err for err in errors))
        self.assertTrue(any("Tier 1 artifact missing required file: docs/quality.md" in err for err in errors))

    def test_invalid_status_rejected(self) -> None:
        fixture_dir = FIXTURES_DIR / "invalid_status"
        ok, errors = validate_artifact(fixture_dir)
        self.assertFalse(ok)
        self.assertTrue(any("Invalid 'status'" in err for err in errors))

    def test_invalid_taxonomy_domain_rejected(self) -> None:
        fixture_dir = FIXTURES_DIR / "invalid_taxonomy"
        ok, errors = validate_artifact(fixture_dir)
        self.assertFalse(ok)
        self.assertTrue(any("Unknown application domain: 'not-a-real-domain'" in err for err in errors))

    def test_invalid_local_first_mode_rejected(self) -> None:
        fixture_dir = FIXTURES_DIR / "invalid_mode"
        ok, errors = validate_artifact(fixture_dir)
        self.assertFalse(ok)
        self.assertTrue(any("Invalid 'local_first_mode'" in err for err in errors))

    def test_nested_valid_artifact_passes(self) -> None:
        nested_dir = FIXTURES_DIR / "nested_discovery" / "patterns" / "nested_valid"
        ok, errors = validate_artifact(nested_dir)
        self.assertTrue(ok, f"Valid nested artifact failed validation: {errors}")
        self.assertEqual(len(errors), 0)

    def test_nested_invalid_artifact_rejected(self) -> None:
        nested_dir = FIXTURES_DIR / "nested_discovery" / "patterns" / "nested_invalid"
        ok, errors = validate_artifact(nested_dir)
        self.assertFalse(ok)
        self.assertTrue(any("Unknown application domain: 'bogus-domain'" in err for err in errors))
        self.assertTrue(any("Invalid 'local_first_mode'" in err for err in errors))
        self.assertTrue(any("Tier 1 artifact missing required file: docs/requirements.md" in err for err in errors))

    def test_artifact_discovery_finds_nested_manifests(self) -> None:
        discovered = find_all_artifacts(FIXTURES_DIR, approved_roots=["nested_discovery"])
        discovered_names = [p.name for p in discovered]
        self.assertIn("nested_valid", discovered_names)
        self.assertIn("nested_invalid", discovered_names)
        self.assertEqual(len(discovered), 2)

    def test_malformed_json_rejected(self) -> None:
        bad_manifest = FIXTURES_DIR / "non_existent" / "artifact.json"
        ok, errors, data = validate_manifest(bad_manifest)
        self.assertFalse(ok)
        self.assertIsNone(data)
        self.assertTrue(any("Manifest file not found" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
