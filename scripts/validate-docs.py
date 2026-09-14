#!/usr/bin/env python3
"""
Lightweight Documentation Quality & Link Validation Script
ai-application-architecture

Validates:
1. Internal markdown link resolution (relative file paths and anchors).
2. Markdown structural integrity (unclosed code fences, heading hierarchy skips).
3. Trailing whitespace detection.

Zero external dependencies (uses standard Python library).
"""

import os
import re
import sys
from pathlib import Path


def get_markdown_files(repo_root: Path) -> list[Path]:
    md_files = []
    for root, dirs, files in os.walk(repo_root):
        # Skip git directory
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            if f.endswith(".md"):
                md_files.append(Path(root) / f)
    return sorted(md_files)


def validate_internal_links(md_files: list[Path], repo_root: Path) -> tuple[int, list[str]]:
    broken_links = []
    total_links = 0
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for file_path in md_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as ex:
            broken_links.append(f"Cannot read {file_path.relative_to(repo_root)}: {ex}")
            continue

        clean_content = re.sub(r"```[\s\S]*?```", "", content)

        for match in link_pattern.finditer(clean_content):
            total_links += 1
            text, target = match.group(1), match.group(2).strip()

            # Ignore external protocols, mailto, and pure anchor links in same file
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue

            # Strip target anchors if present (e.g., path/to/file.md#section)
            clean_target = target.split("#")[0].strip()
            if not clean_target:
                continue

            # Handle file:/// absolute paths
            if clean_target.startswith("file://"):
                target_path = Path(clean_target.replace("file://", ""))
            else:
                target_path = (file_path.parent / clean_target).resolve()

            if not target_path.exists():
                rel_file = file_path.relative_to(repo_root)
                broken_links.append(f"{rel_file}: [{text}]({target}) -> Target not found: {clean_target}")

    return total_links, broken_links


def validate_markdown_structure(md_files: list[Path], repo_root: Path) -> list[str]:
    structure_issues = []

    for file_path in md_files:
        rel_path = file_path.relative_to(repo_root)
        lines = file_path.read_text(encoding="utf-8").splitlines()

        fence_count = 0
        last_heading_level = 0

        for line_num, line in enumerate(lines, start=1):
            # Check for trailing whitespace: allow exactly 2 spaces for standard markdown linebreaks
            if line.endswith("\t"):
                structure_issues.append(f"{rel_path}:{line_num}: Trailing tab detected")
            elif line.endswith(" ") and not (line.endswith("  ") and not line.endswith("   ")):
                structure_issues.append(f"{rel_path}:{line_num}: Trailing whitespace detected (not a 2-space linebreak)")

            # Track code fences
            stripped = line.strip()
            if stripped.startswith("```"):
                fence_count += 1

            # Check heading levels (outside of code fences)
            if fence_count % 2 == 0 and stripped.startswith("#"):
                match = re.match(r"^(#{1,6})\s+", stripped)
                if match:
                    current_level = len(match.group(1))
                    # Heading shouldn't skip levels downwards by more than 1 (e.g. h1 -> h3)
                    if last_heading_level > 0 and current_level > last_heading_level + 1:
                        structure_issues.append(
                            f"{rel_path}:{line_num}: Heading level skipped: h{last_heading_level} -> h{current_level}"
                        )
                    last_heading_level = current_level

        if fence_count % 2 != 0:
            structure_issues.append(f"{rel_path}: Unclosed markdown code fence (found {fence_count} fences)")

    return structure_issues


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    md_files = get_markdown_files(repo_root)

    print(f"=== Markdown Quality & Link Validator ===")
    print(f"Repository Root: {repo_root}")
    print(f"Markdown Files Found: {len(md_files)}")
    print("-" * 50)

    total_links, broken_links = validate_internal_links(md_files, repo_root)
    structure_issues = validate_markdown_structure(md_files, repo_root)

    print(f"Total Internal Links Checked: {total_links}")
    print(f"Broken Links Found: {len(broken_links)}")
    for issue in broken_links:
        print(f"  [BROKEN LINK] {issue}")

    print(f"Structural & Lint Issues Found: {len(structure_issues)}")
    for issue in structure_issues:
        print(f"  [LINT ISSUE] {issue}")

    print("-" * 50)
    if not broken_links and not structure_issues:
        print("RESULT: PASS — All documentation checks succeeded cleanly.")
        return 0
    else:
        print(f"RESULT: FAIL — Found {len(broken_links)} broken links and {len(structure_issues)} structural issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
