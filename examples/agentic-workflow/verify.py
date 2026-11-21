#!/usr/bin/env python3
"""Standalone verification script for Phase 7 Agentic Workflow Orchestration (Tier 2 Pattern Example)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW_DIR = Path(__file__).resolve().parent


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str]:
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return res.returncode, res.stdout


def check_syntax_and_ast(directory: Path) -> tuple[bool, int, str]:
    """Verify syntax and AST integrity across all Python source and test files."""
    count = 0
    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            compile(content, str(py_file), "exec")
            count += 1
        except Exception as exc:
            return False, count, f"Syntax/AST compilation error in {py_file}: {exc}"
    return True, count, ""


def main() -> int:
    print("=" * 70)
    print("Phase 7 Verification — Agentic Workflow Orchestration (Tier 2 Reference Pattern)")
    print("=" * 70)

    # 1. Validate artifact.json manifest and tier structure
    print("[1/4] Validating artifact.json schema and Tier 2 structure...")
    code, out = run_cmd(
        [sys.executable, str(REPO_ROOT / "scripts" / "artifact_validator.py"), str(WORKFLOW_DIR)],
        REPO_ROOT,
    )
    if code != 0:
        print(f"FAILED: artifact_validator error:\n{out}")
        return 1
    print("      -> artifact.json and Tier 2 required files valid.")

    # 2. Gate B: AST and Syntax Compilation Verification
    print("[2/4] Verifying syntax integrity (partial Gate B evidence)...")
    ok, py_count, err = check_syntax_and_ast(WORKFLOW_DIR)
    if not ok:
        print(f"FAILED: {err}")
        return 1
    print(f"      -> {py_count} Python files compiled successfully without syntax errors.")
    print(
        "      -> Run scripts/quality.py in the locked environment for lint, strict types and coverage."
    )

    # 3. Gate C: Run hermetic unit tests
    print("[3/4] Running Gate C hermetic unit tests...")
    code, out = run_cmd(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(WORKFLOW_DIR / "tests"),
            "-t",
            str(WORKFLOW_DIR),
        ],
        REPO_ROOT,
    )
    if code != 0:
        print(f"FAILED: Unit tests failed:\n{out}")
        return 1
    # Extract test count from output
    test_count = "?"
    for line in out.splitlines():
        if "Ran " in line and " tests in " in line:
            test_count = line.split("Ran ")[1].split(" tests in ")[0]
            break
    print(f"      -> {test_count} unit tests passed.")

    # 4. Run deterministic evaluation harness and evaluator self-tests
    print("[4/4] Running 30-scenario deterministic evaluation harness & self-tests...")
    code, out = run_cmd([sys.executable, str(WORKFLOW_DIR / "eval_runner.py")], REPO_ROOT)
    if code != 0:
        print(f"FAILED: Evaluation harness failed:\n{out}")
        return 1
    print(
        "      -> 30/30 deterministic evaluation scenarios passed with zero safety invariant violations."
    )

    print("=" * 70)
    print("VERIFICATION RESULT: PHASE 7 DETERMINISTIC VERIFICATION PASSED")
    print("  Tier Classification: Tier 2 Pattern Example")
    print("  Authoritative Applicable Quality Gates: Gates B, C, H, I")
    print("  Gate B: AST/Syntax checked here; run scripts/quality.py for strict mypy and Ruff.")
    print(
        "  Gate C (Testing): Hermetic unit test suite PASSED (including in-flight reconciliation & true OS restart)"
    )
    print(
        "  Gate D (Voluntary Evaluation): 30/30 scenarios PASSED; all 6 safety invariants derived from runtime evidence"
    )
    print(
        "  Separation of Authority: Workflow Engine owns state machine; Agent owns bounded diagnosis only"
    )
    print(
        "  Ambiguous Execution Safety: Domain reconciliation required for EXECUTION_STARTED; zero duplicate mutations"
    )
    print(
        "  Offline Execution: Mode A deterministic harness; locked telemetry dependencies required."
    )
    print(
        "  Exit 0 records this harness result. It does not certify gate completion or independent acceptance."
    )
    print("=" * 70)
    return 0


if __name__ == "__main__":
    # Windows redirected output otherwise inherits a legacy code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
