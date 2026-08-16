import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect_launch_validation.py"
SPEC = importlib.util.spec_from_file_location("collect_launch_validation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LaunchValidationTests(unittest.TestCase):
    def test_largest_remainder_matches_2025_design(self):
        allocations = MODULE.largest_remainder_allocations(
            {9: 208, 47: 102, 34: 78, 26: 24, 29: 4}, 100
        )
        self.assertEqual(allocations, {9: 50, 47: 24, 34: 19, 26: 6, 29: 1})

    def test_largest_remainder_matches_2026_design(self):
        allocations = MODULE.largest_remainder_allocations(
            {9: 360, 47: 355, 34: 106, 26: 10, 29: 4}, 100
        )
        self.assertEqual(allocations, {9: 43, 47: 43, 34: 13, 26: 1, 29: 0})

    def test_wilson_interval_contains_observed_share(self):
        low, high = MODULE.wilson_interval(50, 100)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_ai_functionality_is_not_ai_development_evidence(self):
        record = {
            "title": "An AI voice integration",
            "opening_post_text": "I built an integration for an AI voice API. Install it via HACS.",
            "category_id": 47,
            "opening_post_words": 50,
            "opening_post_code_elements": 0,
            "github_repositories": ["https://github.com/example/repo"],
        }
        coded = MODULE.classify_record(record)
        self.assertEqual(coded["coding_agent_evidence"], "unknown")

    def test_explicit_agent_development_disclosure_is_confirmed(self):
        record = {
            "title": "A new dashboard card",
            "opening_post_text": "I developed this with Claude Code and published it on GitHub.",
            "category_id": 34,
            "opening_post_words": 50,
            "opening_post_code_elements": 0,
            "github_repositories": ["https://github.com/example/repo"],
        }
        coded = MODULE.classify_record(record)
        self.assertEqual(
            coded["coding_agent_evidence"], "confirmed_explicit_disclosure"
        )


if __name__ == "__main__":
    unittest.main()
