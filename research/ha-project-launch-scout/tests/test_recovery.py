import csv
import hashlib
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RECOVERED = ROOT / "data" / "recovered"
PUBLICATION_DATA = ROOT.parents[1] / "data" / "visualization-data.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RecoveryArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (RECOVERED / "sample-audit-ledger.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            cls.rows = list(csv.DictReader(handle))
        with (RECOVERED / "integration-taxonomy.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            cls.integration_rows = list(csv.DictReader(handle))
        cls.publication = json.loads(PUBLICATION_DATA.read_text(encoding="utf-8"))
        cls.design = json.loads(
            (RECOVERED / "sampling-design.json").read_text(encoding="utf-8")
        )
        cls.manifest = json.loads(
            (RECOVERED / "recovery-manifest.json").read_text(encoding="utf-8")
        )

    def test_recovered_record_counts(self):
        self.assertEqual(len(self.rows), 200)
        self.assertEqual(len({row["topic_id"] for row in self.rows}), 200)
        self.assertEqual(
            sum(row["cohort_year"] == "2025" for row in self.rows), 100
        )
        self.assertEqual(
            sum(row["cohort_year"] == "2026" for row in self.rows), 100
        )
        self.assertEqual(
            sum(row["manual_review_recovered"] == "yes" for row in self.rows),
            124,
        )
        self.assertEqual(
            sum(row["integration_record"] == "yes" for row in self.rows), 53
        )

    def test_sampling_design_preserves_zero_probability_theme_stratum(self):
        self.assertEqual(self.design["seed"], 20260726)
        themes = self.design["cohorts"]["2026"]["strata"]["29"]
        self.assertEqual(themes["population"], 4)
        self.assertEqual(themes["sample"], 0)
        self.assertEqual(themes["inclusion_probability"], 0)
        self.assertIsNone(themes["sample_weight"])

    def test_weighted_integration_estimates_match_publication_inputs(self):
        totals = {}
        for year in ("2025", "2026"):
            totals[year] = round(
                sum(
                    float(row["sample_weight"])
                    for row in self.rows
                    if row["cohort_year"] == year
                    and row["integration_record"] == "yes"
                ),
                2,
            )
        self.assertEqual(totals, {"2025": 84.82, "2026": 272.67})

    def test_generated_file_checksums_match_manifest(self):
        for name, expected in self.manifest["generated_files"].items():
            self.assertEqual(sha256(RECOVERED / name), expected)

    def test_frozen_publication_matches_recovered_ledger(self):
        self.assertEqual(
            sha256(PUBLICATION_DATA), self.manifest["frozen_publication_sha256"]
        )
        frozen = {str(row["id"]): row for row in self.publication["aiTopics"]}
        self.assertEqual(set(frozen), {row["topic_id"] for row in self.rows})
        for row in self.rows:
            source = frozen[row["topic_id"]]
            self.assertEqual(row["title"], source["title"])
            self.assertEqual(row["url"], source["url"])
            self.assertEqual(int(row["cohort_year"]), source["year"])
            self.assertAlmostEqual(float(row["sample_weight"]), source["weight"])
            self.assertEqual(row["launch_eligibility"], source["launchEligibility"])
            self.assertEqual(row["project_type"], source["projectType"])
            self.assertEqual(
                row["coding_agent_evidence"], source["codingAgentEvidence"]
            )

    def test_integration_taxonomy_is_an_exact_ledger_subset(self):
        expected = {
            row["topic_id"]: row
            for row in self.rows
            if row["integration_record"] == "yes"
        }
        observed = {row["topic_id"]: row for row in self.integration_rows}
        self.assertEqual(observed, expected)

    def test_hardware_counts_match_the_published_slice(self):
        counts = {
            year: sum(
                row["cohort_year"] == year
                and row["project_type"] == "hardware_or_physical_build"
                for row in self.rows
            )
            for year in ("2025", "2026")
        }
        self.assertEqual(counts, {"2025": 27, "2026": 17})

    def test_public_ledger_excludes_personal_and_raw_post_fields(self):
        forbidden = {
            "author",
            "username",
            "user_id",
            "email",
            "ip_address",
            "opening_post_text",
            "cooked",
            "raw",
            "replies",
        }
        self.assertTrue(forbidden.isdisjoint(self.rows[0]))
        for row in self.rows:
            parsed = urlparse(row["url"])
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.hostname, "community.home-assistant.io")
            self.assertIn(f"/{row['topic_id']}", parsed.path)

    def test_required_fields_and_cross_field_rules_are_complete(self):
        required = {
            "topic_id",
            "cohort_year",
            "title",
            "url",
            "sample_weight",
            "possible_stratum_category_ids",
            "possible_stratum_category_names",
            "stratum_status",
            "launch_eligibility",
            "project_type",
            "coding_agent_evidence",
            "explicit_disclosure",
            "manual_review_recovered",
            "integration_record",
        }
        integration_fields = {
            "integration_domain",
            "connection_surface",
            "target_scope",
            "integration_target",
            "github_repository_detected",
        }
        for row in self.rows:
            self.assertTrue(all(row[field].strip() for field in required))
            self.assertEqual(
                bool(row["manual_review_note"].strip()),
                row["manual_review_recovered"] == "yes",
            )
            self.assertTrue(
                all(
                    bool(row[field].strip())
                    == (row["integration_record"] == "yes")
                    for field in integration_fields
                )
            )
            self.assertEqual(
                row["explicit_disclosure"] == "true",
                row["coding_agent_evidence"]
                == "confirmed_explicit_disclosure",
            )

    def test_manifest_excludes_internal_machine_and_session_identifiers(self):
        serialized = json.dumps(self.manifest)
        self.assertNotIn("session_id", serialized)
        self.assertNotIn("/Users/", serialized)

    def test_raw_collection_paths_are_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in (
            "data/census/",
            "data/raw/",
            "data/launch-validation/*",
            "!data/launch-validation/manual-review.json",
        ):
            self.assertIn(pattern, ignore)


if __name__ == "__main__":
    unittest.main()
