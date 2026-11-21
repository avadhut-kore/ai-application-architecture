#!/usr/bin/env python3
"""Render every repository Mermaid block with a pinned CLI container."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ghcr.io/mermaid-js/mermaid-cli/mermaid-cli@sha256:18938e53497376d524e04b1fc0bf7b6d61a491ce9ff7032bb2855d57155acb10"


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "documentation_validation", ROOT / "scripts/validate-docs.py"
    )
    assert spec is not None and spec.loader is not None
    validation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validation)
    output = ROOT / ".quality/diagrams"
    output.mkdir(parents=True, exist_ok=True)
    blocks = []
    for path in validation.get_markdown_files(ROOT):
        content = path.read_text(encoding="utf-8")
        for index, match in enumerate(
            re.finditer(r"^```mermaid\s*\n(.*?)^```", content, re.M | re.S), 1
        ):
            blocks.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "number": index,
                    "diagram": match.group(1),
                }
            )
    (output / "manifest.json").write_text(json.dumps(blocks, indent=2), encoding="utf-8")
    document = "# Repository diagrams\n\n" + "\n\n".join(
        f"## Diagram {index}: {row['path']}\n\n```mermaid\n{row['diagram']}```"
        for index, row in enumerate(blocks, 1)
    )
    (output / "all.md").write_text(document, encoding="utf-8")
    print(f"Rendering {len(blocks)} Mermaid blocks", flush=True)
    if not blocks:
        return 0
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--memory",
            "2g",
            "--mount",
            f"type=bind,source={output},target=/data",
            IMAGE,
            "-i",
            "all.md",
            "-o",
            "rendered.md",
            "-j",
            "2",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    (output / "render.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    print(f"Mermaid renderer: exit {result.returncode}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
