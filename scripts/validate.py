#!/usr/bin/env python3
"""Unified Repository & Architecture Validator.

ai-application-architecture

Validates:
1. Physical repository structure and monorepo boundaries.
2. Anti-framework governance and prohibited directory checks.
3. Import boundary enforcement (zero vendor SDKs in building-blocks/contracts).
4. Documentation structure and internal markdown links.
5. Automated test execution for capability contracts.

Zero external dependencies (pure Python standard library).
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import List, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from artifact_validator import (
    find_all_artifacts,
    validate_all_templates,
    validate_artifact,
)

# Mandatory governance files
REQUIRED_GOVERNANCE_FILES = [
    "README.md",
    "VISION.md",
    "SCOPE.md",
    "ROADMAP.md",
    "QUALITY-GATES.md",
    "AGENTS.md",
    ".gitignore",
]

# Mandatory top-level directories
REQUIRED_DIRECTORIES = [
    "apps",
    "building-blocks",
    "platform",
    "docs",
    "scripts",
    "adr",
    "templates",
]

# Prohibited speculative framework directories
PROHIBITED_DIRECTORIES = [
    "enterprise-ai-core",
    "shared-ai-core",
    "ai-framework",
    "model-gateway",
    "ai-gateway",
    "agent-loop",
    "core",
]

# Disallowed vendor SDK imports in contracts
PROHIBITED_CONTRACT_IMPORTS = {
    "openai",
    "anthropic",
    "ollama",
    "langchain",
    "llamaindex",
    "google.generativeai",
    "cohere",
}


def check_structure() -> Tuple[bool, List[str]]:
    """Verify physical repository structure and absence of prohibited dirs."""
    errors: List[str] = []

    for req_file in REQUIRED_GOVERNANCE_FILES:
        if not (REPO_ROOT / req_file).is_file():
            errors.append(f"Missing required governance file: {req_file}")

    for req_dir in REQUIRED_DIRECTORIES:
        if not (REPO_ROOT / req_dir).is_dir():
            errors.append(f"Missing required monorepo directory: {req_dir}")

    for bad_dir in PROHIBITED_DIRECTORIES:
        if (REPO_ROOT / bad_dir).exists():
            errors.append(f"Prohibited speculative directory detected: {bad_dir}")

    # Ensure no empty directories exist (excluding .git)
    for root, dirs, files in os.walk(REPO_ROOT):
        if ".git" in dirs:
            dirs.remove(".git")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        if not dirs and not files and Path(root) != REPO_ROOT:
            rel_dir = Path(root).relative_to(REPO_ROOT)
            errors.append(f"Empty directory detected: {rel_dir}")

    return len(errors) == 0, errors


def check_contract_import_boundaries() -> Tuple[bool, List[str]]:
    """Enforce that building-blocks contracts do not import vendor SDKs or apps."""
    errors: List[str] = []
    contracts_dir = REPO_ROOT / "building-blocks" / "python" / "contracts"

    if not contracts_dir.exists():
        return False, [f"Contracts directory not found: {contracts_dir}"]

    for py_file in contracts_dir.glob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError as ex:
            errors.append(f"Syntax error in {py_file.relative_to(REPO_ROOT)}: {ex}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    if root_pkg in PROHIBITED_CONTRACT_IMPORTS:
                        errors.append(
                            f"{py_file.relative_to(REPO_ROOT)}:{node.lineno}: "
                            f"Prohibited vendor import '{alias.name}' in contract definition."
                        )
                    if root_pkg == "apps":
                        errors.append(
                            f"{py_file.relative_to(REPO_ROOT)}:{node.lineno}: "
                            f"Contract imports from 'apps' directory (inward dependency violation)."
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    if root_pkg in PROHIBITED_CONTRACT_IMPORTS:
                        errors.append(
                            f"{py_file.relative_to(REPO_ROOT)}:{node.lineno}: "
                            f"Prohibited vendor import '{node.module}' in contract definition."
                        )
                    if root_pkg == "apps":
                        errors.append(
                            f"{py_file.relative_to(REPO_ROOT)}:{node.lineno}: "
                            f"Contract imports from 'apps' directory (inward dependency violation)."
                        )

    return len(errors) == 0, errors


def run_doc_validation() -> Tuple[bool, List[str]]:
    """Execute the documentation and link validation script."""
    script_path = REPO_ROOT / "scripts" / "validate-docs.py"
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, [f"Documentation validation failed:\n{proc.stdout}\n{proc.stderr}"]
    return True, []


def run_contract_tests() -> Tuple[bool, List[str]]:
    """Run hermetic contract test suite."""
    test_dir = REPO_ROOT / "building-blocks" / "python" / "tests"
    top_dir = REPO_ROOT / "building-blocks" / "python"

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(test_dir), top_level_dir=str(top_dir))
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    if not result.wasSuccessful():
        errors = [f"Test failures: {len(result.failures)}", f"Test errors: {len(result.errors)}"]
        for failure in result.failures:
            errors.append(f"FAIL: {failure[0]}: {failure[1]}")
        for error in result.errors:
            errors.append(f"ERROR: {error[0]}: {error[1]}")
        return False, errors

    return True, [f"Ran {result.testsRun} unit tests successfully."]


def run_template_and_artifact_validation() -> Tuple[bool, List[str]]:
    """Validate canonical templates and any declared reference artifacts in approved roots."""
    errors: List[str] = []

    # 1. Validate canonical templates in templates/
    templates_root = REPO_ROOT / "templates"
    t_ok, t_errors = validate_all_templates(templates_root)
    if not t_ok:
        errors.extend(t_errors)

    # 2. Recursively discover and validate reference artifacts across approved roots
    artifact_dirs = find_all_artifacts(REPO_ROOT)
    for art_dir in artifact_dirs:
        a_ok, a_errors = validate_artifact(art_dir)
        if not a_ok:
            errors.extend(a_errors)

    return len(errors) == 0, errors


def main() -> int:
    print("=" * 60)
    print("ai-application-architecture — Unified Repository Validator")
    print("=" * 60)
    print(f"Repository Root: {REPO_ROOT}\n")

    overall_success = True

    # 1. Structure & Anti-Framework Check
    print("1. Checking physical repository structure & governance rules...")
    struct_ok, struct_errors = check_structure()
    if struct_ok:
        print("   PASS — Repository structure")
    else:
        print("   FAIL — Repository structure:")
        for err in struct_errors:
            print(f"      - {err}")
        overall_success = False

    # 2. Contract Boundary Enforcement
    print("\n2. Checking contract dependency boundaries (no vendor SDKs)...")
    boundary_ok, boundary_errors = check_contract_import_boundaries()
    if boundary_ok:
        print("   PASS — Contract boundaries")
    else:
        print("   FAIL — Contract boundaries:")
        for err in boundary_errors:
            print(f"      - {err}")
        overall_success = False

    # 3. Documentation Quality & Links
    print("\n3. Validating documentation links & markdown formatting...")
    doc_ok, doc_errors = run_doc_validation()
    if doc_ok:
        print("   PASS — Documentation validation")
    else:
        print("   FAIL — Documentation validation:")
        for err in doc_errors:
            print(f"      - {err}")
        overall_success = False

    # 4. Reference Artifact Templates & Manifests
    print("\n4. Validating reference artifact templates & manifests...")
    templates_ok, template_errors = run_template_and_artifact_validation()
    if templates_ok:
        print("   PASS — Templates & artifact manifests")
    else:
        print("   FAIL — Templates & artifact manifests:")
        for err in template_errors:
            print(f"      - {err}")
        overall_success = False

    # 5. Automated Unit Tests (Contract & Template tests)
    print("\n5. Executing automated unit test suite...")
    tests_ok, test_msgs = run_contract_tests()
    if tests_ok:
        print("   PASS — Automated unit tests")
    else:
        print("   FAIL — Automated unit tests:")
        for err in test_msgs:
            print(f"      - {err}")
        overall_success = False

    print("\n" + "=" * 60)
    if overall_success:
        print("RESULT: REPOSITORY VALIDATION PASSED")
        print("Verified: repository structure, import boundaries, doc links, templates & manifests, unit tests")
        print("=" * 60)
        return 0
    else:
        print("RESULT: REPOSITORY VALIDATION FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
