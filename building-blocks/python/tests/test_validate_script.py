"""Regression tests for cross-platform PYTHONPATH construction in scripts/validate.py."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate


class TestValidateScriptPortability(unittest.TestCase):
    """Verify scripts/validate.py builds cross-platform PYTHONPATH using os.pathsep."""

    def test_build_test_pythonpath_windows_and_posix(self) -> None:
        cases: tuple[tuple[str, PurePath, PurePath, str], ...] = (
            (
                ";",
                PureWindowsPath(r"D:\repo\platform\mcp-adapter"),
                PureWindowsPath(r"D:\repo"),
                r"C:\custom\site-packages",
            ),
            (
                ":",
                PurePosixPath("/repo/platform/mcp-adapter"),
                PurePosixPath("/repo"),
                "/opt/custom/site-packages",
            ),
        )
        for sep, top_dir, repo_root, existing in cases:
            expected_entries = [
                str(top_dir),
                str(repo_root / "building-blocks" / "python"),
                str(repo_root / "examples" / "structured-generation"),
            ]
            with self.subTest(pathsep=sep):
                without_existing = validate.build_test_pythonpath(
                    top_dir=top_dir,
                    repo_root=repo_root,
                    existing_pythonpath="",
                    pathsep=sep,
                )
                self.assertEqual(without_existing, sep.join(expected_entries))
                self.assertEqual(without_existing.split(sep), expected_entries)

                with_existing = validate.build_test_pythonpath(
                    top_dir=top_dir,
                    repo_root=repo_root,
                    existing_pythonpath=existing,
                    pathsep=sep,
                )
                self.assertEqual(with_existing, sep.join([*expected_entries, existing]))
                self.assertEqual(with_existing.split(sep), [*expected_entries, existing])

    def test_run_contract_tests_uses_os_pathsep_and_preserves_env(self) -> None:
        top_dir = REPO_ROOT / "platform" / "mcp-adapter"
        test_dir = top_dir / "tests"
        fake_proc = MagicMock(returncode=0, stderr="Ran 1 test in 0.001s", stdout="")
        expected_base = [
            str(top_dir),
            str(REPO_ROOT / "building-blocks" / "python"),
            str(REPO_ROOT / "examples" / "structured-generation"),
        ]

        for sep, existing in ((";", r"C:\extra\lib"), (":", "/extra/lib")):
            env_patch = {"PYTHONPATH": existing, "VALIDATE_CUSTOM_ENV": "ok"}
            with (
                self.subTest(pathsep=sep),
                patch.dict(os.environ, env_patch, clear=False),
                patch.object(os, "pathsep", sep),
                patch.object(
                    validate,
                    "discover_all_test_suites",
                    return_value=[("platform/mcp-adapter", test_dir, top_dir)],
                ),
                patch.object(validate.subprocess, "run", return_value=fake_proc) as mock_run,
            ):
                ok, msgs = validate.run_contract_tests()
                self.assertTrue(ok, msgs)
                mock_run.assert_called_once()
                passed_env = mock_run.call_args.kwargs["env"]
                self.assertEqual(passed_env["VALIDATE_CUSTOM_ENV"], "ok")
                self.assertEqual(passed_env["PYTHONPATH"], sep.join([*expected_base, existing]))


if __name__ == "__main__":
    unittest.main()
