"""Artifact manifest and structural compliance validator.

ai-application-architecture — Phase 3

Validates reference artifact manifests (`artifact.json`) and required tier structures
using pure Python standard library (zero external dependencies).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VALID_TIERS = {1, 2, 3, 4}
VALID_STATUSES = {
    "planned",
    "experimental",
    "implemented",
    "validated",
    "accepted",
    "deprecated",
}
VALID_LOCAL_FIRST_MODES = {"A", "B", "C", None}

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Mandatory files per tier
TIER_REQUIRED_FILES = {
    1: [
        "artifact.json",
        "README.md",
        "docs/requirements.md",
        "docs/architecture.md",
        "docs/quality.md",
    ],
    2: [
        "artifact.json",
        "README.md",
    ],
    3: [
        "artifact.json",
        "README.md",
    ],
    4: [
        "artifact.json",
        "README.md",
    ],
}


def validate_manifest(manifest_path: Path) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
    """Validate that artifact.json exists, is valid JSON, and adheres to the manifest schema."""
    errors: List[str] = []

    if not manifest_path.is_file():
        return False, [f"Manifest file not found: {manifest_path}"], None

    try:
        content = manifest_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as ex:
        return False, [f"Malformed JSON in {manifest_path}: {ex}"], None
    except Exception as ex:
        return False, [f"Cannot read {manifest_path}: {ex}"], None

    if not isinstance(data, dict):
        return False, [f"Manifest root must be a JSON object, got {type(data).__name__}"], None

    # 1. Name validation
    name = data.get("name")
    if not isinstance(name, str) or not NAME_PATTERN.match(name):
        errors.append(
            f"Invalid 'name': must be a lowercase kebab-case string, got {name!r}"
        )

    # 2. Tier validation
    tier = data.get("tier")
    if tier not in VALID_TIERS:
        errors.append(f"Invalid 'tier': must be one of {sorted(VALID_TIERS)}, got {tier!r}")

    # 3. Status validation
    status = data.get("status")
    if status not in VALID_STATUSES:
        errors.append(
            f"Invalid 'status': must be one of {sorted(VALID_STATUSES)}, got {status!r}"
        )

    # 4. Languages validation
    languages = data.get("languages")
    if not isinstance(languages, list) or not all(isinstance(l, str) for l in languages):
        errors.append(f"Invalid 'languages': must be an array of strings, got {languages!r}")

    # 5. Local-first mode validation
    mode = data.get("local_first_mode")
    if mode not in VALID_LOCAL_FIRST_MODES:
        errors.append(
            f"Invalid 'local_first_mode': must be one of ['A', 'B', 'C', null], got {mode!r}"
        )

    # 6. Taxonomy collections validation
    for tax_field in ("application_domains", "intelligence_patterns", "architecture_patterns"):
        val = data.get(tax_field)
        if val is not None and (not isinstance(val, list) or not all(isinstance(item, str) for item in val)):
            errors.append(f"Invalid '{tax_field}': must be an array of strings if specified")

    return len(errors) == 0, errors, data if len(errors) == 0 else None


def validate_artifact_structure(artifact_dir: Path, tier: int) -> Tuple[bool, List[str]]:
    """Verify that mandatory files required by the declared tier are present."""
    errors: List[str] = []
    required_files = TIER_REQUIRED_FILES.get(tier, [])

    for rel_file in required_files:
        target_path = artifact_dir / rel_file
        if not target_path.exists():
            errors.append(
                f"Tier {tier} artifact missing required file: {rel_file}"
            )

    return len(errors) == 0, errors


def validate_artifact(artifact_dir: Path) -> Tuple[bool, List[str]]:
    """Complete validation of an artifact directory (manifest + tier structure)."""
    manifest_path = artifact_dir / "artifact.json"
    manifest_ok, manifest_errors, data = validate_manifest(manifest_path)

    if not manifest_ok or data is None:
        return False, [f"{artifact_dir.name}: {err}" for err in manifest_errors]

    tier = data["tier"]
    struct_ok, struct_errors = validate_artifact_structure(artifact_dir, tier)

    if not struct_ok:
        return False, [f"{artifact_dir.name}: {err}" for err in struct_errors]

    return True, []


def validate_all_templates(templates_root: Path) -> Tuple[bool, List[str]]:
    """Validate all canonical templates in the templates/ directory."""
    errors: List[str] = []
    expected_templates = {
        "reference-application": 1,
        "pattern-example": 2,
        "platform-component": 3,
        "template-artifact": 4,
    }

    if not templates_root.is_dir():
        return False, [f"Templates root directory not found: {templates_root}"]

    # Ensure README exists
    if not (templates_root / "README.md").is_file():
        errors.append("Missing required governance document: templates/README.md")

    for dir_name, expected_tier in expected_templates.items():
        template_dir = templates_root / dir_name
        if not template_dir.is_dir():
            errors.append(f"Missing required template archetype: templates/{dir_name}")
            continue

        ok, t_errors = validate_artifact(template_dir)
        if not ok:
            errors.extend(t_errors)
            continue

        # Verify declared tier matches expected
        _, _, data = validate_manifest(template_dir / "artifact.json")
        if data and data.get("tier") != expected_tier:
            errors.append(
                f"Template {dir_name} declared tier {data.get('tier')}, expected {expected_tier}"
            )

    return len(errors) == 0, errors
