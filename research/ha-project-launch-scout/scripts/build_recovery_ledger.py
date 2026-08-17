#!/usr/bin/env python3
"""Build a transparent audit ledger from the frozen publication snapshot.

The resulting files distinguish exact recovered values from fields inferred
from the published sample weights. They do not recreate missing raw forum
snapshots or pretend that live forum content is the original snapshot.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


SEED = 20260726
CATEGORY_NAMES = {
    9: "Share your Projects!",
    47: "Custom Integrations",
    34: "Dashboards & Frontend",
    29: "Themes",
    26: "Scripts",
}
DESIGN = {
    2025: {
        9: {"population": 208, "sample": 50},
        47: {"population": 102, "sample": 24},
        34: {"population": 78, "sample": 19},
        26: {"population": 24, "sample": 6},
        29: {"population": 4, "sample": 1},
    },
    2026: {
        9: {"population": 360, "sample": 43},
        47: {"population": 355, "sample": 43},
        34: {"population": 106, "sample": 13},
        26: {"population": 10, "sample": 1},
        29: {"population": 4, "sample": 0},
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def possible_categories(year: int, weight: float) -> list[int]:
    matches = []
    for category_id, stratum in DESIGN[year].items():
        sample = stratum["sample"]
        if not sample:
            continue
        expected = stratum["population"] / sample
        if abs(expected - weight) < 1e-9:
            matches.append(category_id)
    if not matches:
        raise ValueError(f"No sampling stratum matches {year=} {weight=}")
    return matches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("visualization_data", type=Path)
    parser.add_argument(
        "--research-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()

    root = args.research_root
    output = root / "data" / "recovered"
    frozen = json.loads(args.visualization_data.read_text(encoding="utf-8"))
    manual_payload = json.loads(
        (root / "data/launch-validation/manual-review.json").read_text(
            encoding="utf-8"
        )
    )
    taxonomy_payload = json.loads(
        (root / "data/insights/integration-taxonomy-review.json").read_text(
            encoding="utf-8"
        )
    )
    manual = {int(key): value for key, value in manual_payload["topics"].items()}
    taxonomy = {
        int(key): value for key, value in taxonomy_payload["topics"].items()
    }
    integrations = {int(row["id"]): row for row in frozen["integrations"]}

    if len(frozen["aiTopics"]) != 200:
        raise RuntimeError("Frozen publication snapshot no longer has 200 topics")
    if len(integrations) != 53 or set(integrations) != set(taxonomy):
        raise RuntimeError("Recovered taxonomy does not match the frozen 53 records")

    rows: list[dict[str, Any]] = []
    for source in sorted(
        frozen["aiTopics"], key=lambda row: (int(row["year"]), int(row["id"]))
    ):
        topic_id = int(source["id"])
        year = int(source["year"])
        weight = float(source["weight"])
        possible = possible_categories(year, weight)
        review = manual.get(topic_id)
        integration = integrations.get(topic_id)

        if review:
            if review["launch_eligibility"] != source["launchEligibility"]:
                raise RuntimeError(f"Launch code mismatch for topic {topic_id}")
            if review["project_type"] != source["projectType"]:
                raise RuntimeError(f"Project type mismatch for topic {topic_id}")
            review_ai = review.get("coding_agent_evidence")
            if review_ai and review_ai != source["codingAgentEvidence"]:
                raise RuntimeError(f"AI evidence mismatch for topic {topic_id}")

        if integration:
            expected = taxonomy[topic_id]
            observed = [
                integration["domain"],
                integration["surface"],
                integration["scope"],
                integration["target"],
            ]
            if expected != observed:
                raise RuntimeError(f"Integration taxonomy mismatch for {topic_id}")

        rows.append(
            {
                "topic_id": topic_id,
                "cohort_year": year,
                "title": source["title"],
                "url": source["url"],
                "sample_weight": f"{weight:.15g}",
                "possible_stratum_category_ids": "|".join(map(str, possible)),
                "possible_stratum_category_names": "|".join(
                    CATEGORY_NAMES[value] for value in possible
                ),
                "stratum_status": "exact_from_weight"
                if len(possible) == 1
                else "ambiguous_from_weight",
                "launch_eligibility": source["launchEligibility"],
                "project_type": source["projectType"],
                "coding_agent_evidence": source["codingAgentEvidence"],
                "explicit_disclosure": str(bool(source["explicitDisclosure"])).lower(),
                "manual_review_recovered": "yes" if review else "no",
                "manual_review_note": review["review_note"] if review else "",
                "integration_record": "yes" if integration else "no",
                "integration_domain": integration["domain"] if integration else "",
                "connection_surface": integration["surface"] if integration else "",
                "target_scope": integration["scope"] if integration else "",
                "integration_target": integration["target"] if integration else "",
                "github_repository_detected": (
                    str(bool(integration["github"])).lower() if integration else ""
                ),
            }
        )

    if len({row["topic_id"] for row in rows}) != 200:
        raise RuntimeError("Recovered audit ledger contains duplicate topic IDs")
    for year in (2025, 2026):
        if sum(row["cohort_year"] == year for row in rows) != 100:
            raise RuntimeError(f"Recovered cohort {year} does not contain 100 rows")
    if sum(row["manual_review_recovered"] == "yes" for row in rows) != 124:
        raise RuntimeError("Expected 124 recovered manual-review decisions")
    if sum(row["integration_record"] == "yes" for row in rows) != 53:
        raise RuntimeError("Expected 53 recovered integration records")

    write_csv(output / "sample-audit-ledger.csv", rows)
    integration_rows = [row for row in rows if row["integration_record"] == "yes"]
    write_csv(output / "integration-taxonomy.csv", integration_rows)

    design_json = {
        "status": "exact_recovery_from_original_sampling_script",
        "seed": SEED,
        "cohorts": {
            str(year): {
                "window": f"{year}-01-01 through {year}-03-31",
                "population": sum(item["population"] for item in strata.values()),
                "sample": sum(item["sample"] for item in strata.values()),
                "strata": {
                    str(category_id): {
                        "category_name": CATEGORY_NAMES[category_id],
                        **values,
                        "inclusion_probability": (
                            values["sample"] / values["population"]
                        ),
                        "sample_weight": (
                            values["population"] / values["sample"]
                            if values["sample"]
                            else None
                        ),
                    }
                    for category_id, values in strata.items()
                },
            }
            for year, strata in DESIGN.items()
        },
        "allocation": "Proportional stratified sample with largest-remainder allocation",
        "selection": (
            "Within each category, sort by topic_id and sample with "
            "random.Random(seed + year * 1000 + category_id)."
        ),
        "weight_formula": "stratum_population / stratum_sample",
        "known_limit": (
            "The four Q1 2026 Theme topics received an allocation of zero and "
            "therefore have zero inclusion probability in this sample."
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    design_path = output / "sampling-design.json"
    design_path.write_text(
        json.dumps(design_json, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    weighted_integrations = {
        str(year): round(
            sum(
                float(row["sample_weight"])
                for row in integration_rows
                if row["cohort_year"] == year
            ),
            2,
        )
        for year in (2025, 2026)
    }
    manifest = {
        "recovery_date": "2026-08-17",
        "frozen_publication_sha256": sha256(args.visualization_data),
        "records": {
            "sample_topics": len(rows),
            "manual_review_decisions": len(manual),
            "integration_taxonomy_records": len(integrations),
        },
        "weighted_integration_estimates_before_whole_number_rounding": (
            weighted_integrations
        ),
        "exactly_recovered": [
            "Frozen final labels, titles, URLs and weights for 200 sampled topics",
            "Manual-review decisions and notes for 124 topics",
            "Domain, connection-surface and scope codes for 53 integrations",
            "Sampling seed, strata, allocations and weighting formula",
        ],
        "not_recovered": [
            "Original raw category-listing JSON files",
            "Original opening-post JSON and HTML snapshots",
            "Exact category IDs for rows whose published weight maps to more than one stratum",
            "Generated intermediate CSV and summary files not embedded in the task transcript",
        ],
        "generated_files": {
            "sample-audit-ledger.csv": sha256(output / "sample-audit-ledger.csv"),
            "integration-taxonomy.csv": sha256(output / "integration-taxonomy.csv"),
            "sampling-design.json": sha256(design_path),
        },
    }
    (output / "recovery-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
