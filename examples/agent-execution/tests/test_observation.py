"""Bounded tool observation regressions."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "building-blocks/python"), str(ROOT / "examples/agent-execution")]
from agent.observation import (
    bounded_json,
    format_observation,
    TRUNCATION_MARKER,
    OBSERVATION_BEGIN,
    OBSERVATION_END,
)


class TestBoundedSerialization(unittest.TestCase):
    def test_large_strings_containers_and_escaping_stay_bounded(self) -> None:
        for value in ("اردو\n" * 100_000, {"x": "x" * 1_000_000}, list(range(10000))):
            text, truncated = bounded_json(value, 256)
            self.assertTrue(truncated)
            self.assertLessEqual(len(text), 256)
            self.assertIn(TRUNCATION_MARKER, text)
        value = {"x": [1, True, None, 1.5, "text"]}
        text, truncated = bounded_json(value, 256)
        self.assertFalse(truncated)
        self.assertEqual(json.loads(text), value)

    def test_invalid_json_and_cycles_fail_explicitly(self) -> None:
        circular = {}
        circular["self"] = circular
        for value in (object(), float("nan"), {1: "key"}, circular):
            with self.assertRaises((TypeError, ValueError)):
                bounded_json(value, 256)

    def test_observation_framing_is_preserved_at_small_limits(self) -> None:
        minimum = len(OBSERVATION_BEGIN) + len(OBSERVATION_END) + len(TRUNCATION_MARKER)
        for limit in range(minimum, minimum + 60):
            text = format_observation("x" * 1000, limit)
            self.assertLessEqual(len(text), limit)
            self.assertTrue(text.startswith(OBSERVATION_BEGIN))
            self.assertTrue(text.endswith(OBSERVATION_END))
            self.assertIn(TRUNCATION_MARKER, text)
