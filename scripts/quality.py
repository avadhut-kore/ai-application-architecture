"""Executable static, coverage and security gates for the active Python artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from validate import discover_all_test_suites

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / os.environ.get("QUALITY_OUTPUT", ".quality")
PACKAGES = {
    "building-blocks/python": ["contracts", "ai_telemetry"],
    "examples/agent-execution": ["agent"],
    "examples/agentic-workflow": ["workflow"],
    "examples/rag": ["rag"],
    "examples/structured-generation": ["structured_generation"],
    "examples/ai-evaluation": [],
    "platform/mcp-adapter": ["mcp_adapter"],
    "platform/ollama-adapter": ["ollama_adapter"],
    "platform/ollama-embedding-adapter": ["ollama_embedding_adapter"],
    "scripts": [],
}


def run(
    label: str, command: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None
) -> bool:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (OUTPUT / f"{label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    print(f"{label}: exit {result.returncode}", flush=True)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--coverage-only", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["MYPYPATH"] = os.pathsep.join(str(ROOT / directory) for directory in PACKAGES)
    outcomes: dict[str, Any] = {}
    if not args.coverage_only:
        outcomes["format"] = run(
            "format", [sys.executable, "-m", "ruff", "format", "--check", "."], env=env
        )
        outcomes["ruff"] = run("ruff", [sys.executable, "-m", "ruff", "check", "."], env=env)
        for rel, packages in PACKAGES.items():
            key = rel.replace("/", "-")
            entrypoints = [
                path.name for path in (ROOT / rel).glob("*.py") if path.name != "__init__.py"
            ]
            outcomes[f"typing-{key}"] = run(
                f"typing-{key}",
                [
                    sys.executable,
                    "-m",
                    "mypy",
                    "--strict",
                    "--explicit-package-bases",
                    *packages,
                    *entrypoints,
                ],
                ROOT / rel,
                env,
            )
    if not args.static_only:
        for old in OUTPUT.glob("*.coverage*"):
            old.unlink()
        for old in OUTPUT.glob("combined*"):
            old.unlink()
        coverage: dict[str, Any] = {}
        for label, tests, top in discover_all_test_suites(ROOT):
            rel = top.relative_to(ROOT).as_posix()
            packages = PACKAGES.get(rel, [])
            key = rel.replace("/", "-")
            source = ",".join(
                str(ROOT / directory / package)
                for directory, names in PACKAGES.items()
                for package in names
            )
            source += "," + str(ROOT / "examples/ai-evaluation")
            suite_env = dict(env)
            suite_env["COVERAGE_FILE"] = str(OUTPUT / f"{key}.coverage")
            suite_env["PYTHONPATH"] = os.pathsep.join(
                [
                    str(top),
                    str(ROOT / "building-blocks/python"),
                    str(ROOT / "examples/structured-generation"),
                ]
            )
            passed = run(
                f"tests-{key}",
                [
                    sys.executable,
                    "-m",
                    "coverage",
                    "run",
                    "--source",
                    source,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    str(tests),
                    "-t",
                    str(top),
                ],
                env=suite_env,
            )
            outcomes[f"tests-{key}"] = passed
        combined_env = dict(env, COVERAGE_FILE=str(OUTPUT / "combined"))
        files = [str(path) for path in OUTPUT.glob("*.coverage*")]
        outcomes["coverage-combine"] = run(
            "coverage-combine",
            [sys.executable, "-m", "coverage", "combine", "--keep", *files],
            env=combined_env,
        )
        report = OUTPUT / "coverage.json"
        outcomes["coverage-export"] = run(
            "coverage-export",
            [sys.executable, "-m", "coverage", "json", "-o", str(report)],
            env=combined_env,
        )
        failures = []
        artifact_totals: dict[str, list[int]] = {}
        if report.exists():
            data = json.loads(report.read_text())
            for filename, value in data["files"].items():
                path = filename.replace("\\", "/")
                if "/tests/" in path or path.endswith(
                    ("/test_doubles.py", "/verify.py", "/demo.py")
                ):
                    continue
                if (
                    path.endswith("/__init__.py")
                    and path != "building-blocks/python/ai_telemetry/__init__.py"
                ):
                    continue
                summary = value["summary"]
                artifact = next((rel for rel in PACKAGES if path.startswith(rel + "/")), None)
                if artifact:
                    totals = artifact_totals.setdefault(artifact, [0, 0, 0, 0])
                    for index, field in enumerate(
                        ("covered_lines", "num_statements", "covered_branches", "num_branches")
                    ):
                        totals[index] += summary[field]
                statements = summary["num_statements"]
                percentage = 100 * summary["covered_lines"] / statements if statements else 100
                coverage[path] = {"statement_percent": percentage}
                if percentage < 85:
                    failures.append(f"{path}: {percentage:.2f}%")
        outcomes["coverage-modules"] = not failures
        if failures:
            print("Below 85% statements: " + ", ".join(failures), flush=True)
        (OUTPUT / "coverage-summary.json").write_text(
            json.dumps(coverage, indent=2), encoding="utf-8"
        )
        artifacts = {}
        for artifact, (lines, statements, branches, total_branches) in artifact_totals.items():
            tier3 = artifact.startswith(("platform/", "building-blocks/"))
            line_percent = 100 * lines / statements if statements else 100
            branch_percent = 100 * branches / total_branches if total_branches else 100
            required_lines, required_branches = (85, 80) if tier3 else (70, 65)
            artifacts[artifact] = {
                "statement_percent": line_percent,
                "branch_percent": branch_percent,
                "required_lines": required_lines,
                "required_branches": required_branches,
            }
            if line_percent < required_lines or branch_percent < required_branches:
                failures.append(
                    f"{artifact}: lines={line_percent:.2f}%, branches={branch_percent:.2f}%"
                )
        outcomes["coverage-artifacts"] = not failures
        (OUTPUT / "artifact-coverage.json").write_text(
            json.dumps(artifacts, indent=2), encoding="utf-8"
        )
        if not outcomes["coverage-artifacts"]:
            print("Coverage targets not met: " + ", ".join(failures), flush=True)
    (OUTPUT / "results.json").write_text(json.dumps(outcomes, indent=2), encoding="utf-8")
    return 0 if all(outcomes.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
