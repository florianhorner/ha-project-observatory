#!/usr/bin/env python3
"""Reproducible launch-validation sample for the HA project-topic census.

This stage opens only the original opening post for 100 proportionally
stratified Q1 2025 topics and 100 Q1 2026 topics. It deliberately does not
collect replies, repository contents, quality signals, or traction.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


BASE_URL = "https://community.home-assistant.io"
SEED = 20260726
COHORTS = (2025, 2026)
SAMPLE_PER_COHORT = 100
CATEGORY_NAMES = {
    9: "Share your Projects!",
    47: "Custom Integrations",
    34: "Dashboards & Frontend",
    29: "Themes",
    26: "Scripts",
}

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "data" / "census"
OUT = ROOT / "data" / "launch-validation"
RAW = ROOT / "data" / "raw" / "launch-validation"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def largest_remainder_allocations(
    strata: dict[int, int], sample_size: int
) -> dict[int, int]:
    total = sum(strata.values())
    if sample_size > total:
        raise ValueError("Sample cannot exceed population")
    exact = {key: sample_size * count / total for key, count in strata.items()}
    allocated = {key: math.floor(value) for key, value in exact.items()}
    remaining = sample_size - sum(allocated.values())
    order = sorted(
        strata,
        key=lambda key: (exact[key] - allocated[key], strata[key], -key),
        reverse=True,
    )
    for key in order[:remaining]:
        allocated[key] += 1
    return allocated


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_sample() -> None:
    source = CENSUS / "forum-project-topics.csv"
    rows = read_csv(source)
    selected: list[dict[str, Any]] = []
    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source.relative_to(ROOT)),
        "source_sha256": sha256_file(source),
        "seed": SEED,
        "sampling": "proportional stratified random sample; largest remainder allocation",
        "sample_per_cohort": SAMPLE_PER_COHORT,
        "cohorts": {},
    }

    for year in COHORTS:
        cohort = [
            row
            for row in rows
            if row["created_at"] >= f"{year}-01-01"
            and row["created_at"] < f"{year}-04-01"
        ]
        by_category: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in cohort:
            by_category[int(row["category_id"])].append(row)
        populations = {key: len(value) for key, value in by_category.items()}
        allocations = largest_remainder_allocations(populations, SAMPLE_PER_COHORT)

        year_selected: list[dict[str, Any]] = []
        for category_id in sorted(by_category):
            population = sorted(
                by_category[category_id], key=lambda row: int(row["topic_id"])
            )
            rng = random.Random(SEED + year * 1000 + category_id)
            chosen = rng.sample(population, allocations[category_id])
            for row in chosen:
                year_selected.append(
                    {
                        "cohort_year": year,
                        "topic_id": row["topic_id"],
                        "created_at": row["created_at"],
                        "category_id": category_id,
                        "category_name": row["category_name"],
                        "title": row["title"],
                        "slug": row["slug"],
                        "url": row["url"],
                        "tags": row["tags"],
                        "stratum_population": populations[category_id],
                        "stratum_sample": allocations[category_id],
                        "inclusion_probability": (
                            allocations[category_id] / populations[category_id]
                        ),
                        "sample_weight": (
                            populations[category_id] / allocations[category_id]
                            if allocations[category_id]
                            else ""
                        ),
                    }
                )

        random.Random(SEED + year).shuffle(year_selected)
        for index, row in enumerate(year_selected, start=1):
            row["sample_order"] = index
        selected.extend(year_selected)
        manifest["cohorts"][str(year)] = {
            "population": len(cohort),
            "sample": len(year_selected),
            "strata": {
                str(category_id): {
                    "category_name": CATEGORY_NAMES[category_id],
                    "population": populations[category_id],
                    "sample": allocations[category_id],
                }
                for category_id in sorted(populations)
            },
        }

    selected.sort(key=lambda row: (row["cohort_year"], row["sample_order"]))
    if Counter(row["cohort_year"] for row in selected) != Counter({2025: 100, 2026: 100}):
        raise RuntimeError("Selection did not produce exactly 100 records per cohort")
    if len({row["topic_id"] for row in selected}) != 200:
        raise RuntimeError("Selection contains duplicate topics")

    write_csv(OUT / "sample.csv", selected)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sample-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


def fetch_json(
    url: str, cache_path: Path, *, allow_missing: bool = False
) -> dict[str, Any]:
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "HA-project-launch-validation/0.1 (bounded public-data research)",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.load(response)
            cache_path.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            time.sleep(0.20)
            return payload
        except urllib.error.HTTPError as exc:
            if allow_missing and exc.code in {403, 404}:
                return {}
            if exc.code == 429 and attempt < 4:
                time.sleep(3 * (attempt + 1))
                continue
            if 400 <= exc.code < 500 or attempt == 4:
                raise RuntimeError(f"Failed to fetch {url}: HTTP {exc.code}") from exc
            time.sleep(2**attempt)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 4:
                raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


class LinkAndTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_parts: list[str] = []
        self.code_blocks = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(html.unescape(href))
        if tag in {"pre", "code"}:
            self.code_blocks += 1
        if tag in {"p", "li", "br", "h1", "h2", "h3"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)


class PreviousRevisionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_previous = False
        self.parts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        classes = (dict(attrs).get("class") or "").split()
        if tag == "td" and "--previous" in classes:
            self.in_previous = True
        elif self.in_previous and tag in {"br", "p", "li", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_previous:
            self.in_previous = False
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.in_previous:
            self.parts.append(data)


def cooked_text_links_and_code(cooked: str) -> tuple[str, list[str], int]:
    parser = LinkAndTextParser()
    parser.feed(cooked or "")
    text = re.sub(r"[ \t]+", " ", "".join(parser.text_parts))
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return text, list(dict.fromkeys(parser.links)), parser.code_blocks


def urls_in_text(text: str) -> list[str]:
    values = re.findall(r"https?://[^\s<>()\]\[\"']+", text)
    return list(dict.fromkeys(value.rstrip(".,;:") for value in values))


def github_repositories(links: Iterable[str], text: str) -> list[str]:
    candidates = list(links) + re.findall(
        r"(?:https?://)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", text
    )
    repositories: list[str] = []
    for candidate in candidates:
        if candidate.startswith("github.com/"):
            candidate = f"https://{candidate}"
        match = re.match(r"https?://github\.com/([^/]+)/([^/#?\s]+)", candidate)
        if not match:
            continue
        repository = (
            f"https://github.com/{match.group(1)}/"
            f"{match.group(2).removesuffix('.git').rstrip('.,;:')}"
        )
        if repository not in repositories:
            repositories.append(repository)
    return repositories


def first_post(payload: dict[str, Any]) -> dict[str, Any]:
    posts = payload.get("post_stream", {}).get("posts", [])
    if not posts:
        raise RuntimeError("Topic payload contains no posts")
    return min(posts, key=lambda post: int(post.get("post_number", 10**9)))


def run_topics() -> None:
    sample = read_csv(OUT / "sample.csv")
    records: list[dict[str, Any]] = []
    edited = 0
    revision_fallbacks = 0
    for index, row in enumerate(sample, start=1):
        topic_id = int(row["topic_id"])
        payload = fetch_json(
            f"{BASE_URL}/t/{topic_id}.json", RAW / "topics" / f"{topic_id}.json"
        )
        post = first_post(payload)
        current_text, current_links, code_blocks = cooked_text_links_and_code(
            post.get("cooked", "")
        )
        text = current_text
        links = current_links
        source = "current_unedited"
        version = int(post.get("version", 1))
        if version > 1:
            edited += 1
            revision = fetch_json(
                f"{BASE_URL}/posts/{int(post['id'])}/revisions/2.json",
                RAW / "revisions" / f"{topic_id}-revision-2.json",
                allow_missing=True,
            )
            side_by_side = (
                revision.get("body_changes", {}).get("side_by_side_markdown", "")
            )
            parser = PreviousRevisionParser()
            parser.feed(side_by_side)
            reconstructed = re.sub(
                r"\n\s*\n+", "\n", "".join(parser.parts)
            ).strip()
            if reconstructed:
                text = html.unescape(reconstructed)
                links = urls_in_text(text)
                source = "original_previous_column_revision_2"
            else:
                source = "current_revision_fallback"
                revision_fallbacks += 1

        repos = github_repositories(links, text)
        records.append(
            {
                "topic_id": topic_id,
                "cohort_year": int(row["cohort_year"]),
                "category_id": int(row["category_id"]),
                "title": row["title"],
                "url": row["url"],
                "current_version": version,
                "content_source": source,
                "opening_post_words": len(text.split()),
                "opening_post_code_elements": code_blocks,
                "links": links,
                "github_repositories": repos,
                "opening_post_text": text,
            }
        )
        print(
            f"[{index:03d}/200] {topic_id} v{version} "
            f"{source} {row['title'][:55]}"
        )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "opening-posts.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    summary = {
        "topics": len(records),
        "edited_topics": edited,
        "revision_fallbacks": revision_fallbacks,
        "topic_bodies_only": True,
        "replies_collected": False,
        "repositories_opened": False,
    }
    (OUT / "collection-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


LAUNCH_PATTERNS = [
    r"\bi (?:have )?(?:built|created|made|wrote|developed|released|published)\b",
    r"\b(?:announcing|introducing|released|launching)\b",
    r"\bmy (?:new )?(?:project|integration|card|dashboard|theme|blueprint|add-on|addon|tool)\b",
    r"\b(?:happy|excited|proud) to (?:share|announce|release)\b",
    r"\bi(?:'|’)d like to share\b",
    r"\bhere(?:'|’)s (?:a|my)\b",
]
SUPPORT_PATTERNS = [
    r"\b(?:need|looking for|asking for|requesting) help\b",
    r"\b(?:not working|doesn(?:'|’)t work|issue with|problem with)\b",
    r"\bhow (?:do|can|could|would) i\b",
    r"\bcan (?:someone|anyone) (?:help|tell|explain)\b",
    r"\bdoes (?:anyone|somebody) know\b",
    r"\bis there (?:an?|any)\b",
    r"\bfeature request\b",
]
WIP_PATTERNS = [
    r"\b(?:idea|concept) (?:for|only)\b",
    r"\bi (?:am|(?:'|’)m) (?:thinking|planning|considering)\b",
    r"\bi would like to (?:build|create|make|develop)\b",
    r"\blooking for (?:developers|contributors|testers)\b",
]
REPRODUCTION_PATTERNS = [
    r"\b(?:install|installation|download|repository|source code|github|gitlab|hacs)\b",
    r"\b(?:copy|paste|add) (?:the |this )?(?:yaml|code|configuration)\b",
    r"\b(?:configuration|setup) (?:steps|instructions|guide)\b",
    r"\b(?:available|published) (?:on|at|via|through) (?:github|hacs|gitlab)\b",
]
EXPLICIT_AI_PATTERNS = [
    r"\b(?:built|made|developed|generated|coded|written)(?: this| it| the project)? "
    r"(?:using|with|by) "
    r"(?:claude(?: code)?|cursor|copilot|chatgpt|codex|gemini)\b",
    r"\b(?:claude(?: code)?|cursor|copilot|chatgpt|codex|gemini) "
    r"(?:built|generated|wrote|coded|developed|helped (?:build|write|code))\b",
    r"\bai[- ](?:generated|written|coded|assisted|developed)\b",
]


def any_pattern(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def classify_type(category_id: int, text: str) -> str:
    if category_id == 47:
        return "custom_integration_or_device_bridge"
    if category_id in {34, 29}:
        return "dashboard_card_theme_or_frontend"
    if category_id == 26:
        return "automation_blueprint_script_or_config"

    lowered = text.lower()
    keyword_groups = [
        (
            "hardware_or_physical_build",
            [
                "esp32",
                "esp8266",
                "esphome",
                "raspberry pi",
                "pcb",
                "3d print",
                "sensor build",
                "hardware",
            ],
        ),
        (
            "dashboard_card_theme_or_frontend",
            [
                "lovelace",
                "dashboard",
                "custom card",
                "frontend",
                "theme",
                "card-mod",
            ],
        ),
        (
            "custom_integration_or_device_bridge",
            [
                "custom integration",
                "custom_component",
                "integration for",
                "hacs integration",
                "device bridge",
            ],
        ),
        (
            "automation_blueprint_script_or_config",
            ["blueprint", "automation", "yaml package", "script", "configuration package"],
        ),
        (
            "addon_application_developer_or_ops_tool",
            [
                "add-on",
                "addon",
                "docker",
                "application",
                "developer tool",
                "monitoring tool",
                "proxy",
                "mqtt bridge",
                "companion app",
            ],
        ),
        (
            "tutorial_or_reproducible_system_build",
            ["tutorial", "step-by-step", "how-to", "guide"],
        ),
    ]
    for project_type, keywords in keyword_groups:
        if any(keyword in lowered for keyword in keywords):
            return project_type
    return "other_or_unclear"


def classify_record(record: dict[str, Any]) -> dict[str, Any]:
    title = str(record["title"])
    body = str(record["opening_post_text"])
    combined = f"{title}\n{body}"
    launch_language = any_pattern(LAUNCH_PATTERNS, combined)
    support_language = any_pattern(SUPPORT_PATTERNS, combined)
    wip_language = any_pattern(WIP_PATTERNS, combined)
    reproduction_language = any_pattern(REPRODUCTION_PATTERNS, combined)
    has_repo = bool(record["github_repositories"])
    has_code = int(record["opening_post_code_elements"]) > 0
    words = int(record["opening_post_words"])
    usable_evidence = has_repo or has_code or reproduction_language

    if support_language and not (launch_language and usable_evidence):
        eligibility = "not_launch"
        reason = "support_or_solution_request"
    elif wip_language and not usable_evidence:
        eligibility = "not_launch"
        reason = "idea_or_wip_without_usable_artifact"
    elif words < 20 and not usable_evidence:
        eligibility = "not_launch"
        reason = "insufficient_opening_material"
    elif launch_language and usable_evidence:
        eligibility = "launch"
        reason = "project_presentation_with_artifact_or_reproduction_evidence"
    elif int(record["category_id"]) != 9 and usable_evidence:
        eligibility = "launch"
        reason = "project_subcategory_with_artifact_or_reproduction_evidence"
    elif usable_evidence and words >= 100 and not support_language:
        eligibility = "launch"
        reason = "substantive_reproducible_project_post"
    else:
        eligibility = "uncertain"
        reason = "opening_post_requires_human_judgment"

    ai_evidence = (
        "confirmed_explicit_disclosure"
        if any_pattern(EXPLICIT_AI_PATTERNS, combined)
        else "unknown"
    )
    return {
        "initial_launch_eligibility": eligibility,
        "initial_reason": reason,
        "initial_project_type": classify_type(int(record["category_id"]), combined),
        "linked_github_repository": "|".join(record["github_repositories"]),
        "coding_agent_evidence": ai_evidence,
        "signal_launch_language": launch_language,
        "signal_support_language": support_language,
        "signal_wip_language": wip_language,
        "signal_reproduction_language": reproduction_language,
        "signal_code_elements": has_code,
    }


def load_opening_posts() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (OUT / "opening-posts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def run_initial_classification() -> None:
    sample = {int(row["topic_id"]): row for row in read_csv(OUT / "sample.csv")}
    records = load_opening_posts()
    coded: list[dict[str, Any]] = []
    for record in records:
        row = sample[int(record["topic_id"])]
        coded.append(
            {
                "topic_id": record["topic_id"],
                "cohort_year": record["cohort_year"],
                "sample_order": row["sample_order"],
                "category_id": record["category_id"],
                "category_name": CATEGORY_NAMES[int(record["category_id"])],
                "title": record["title"],
                "url": record["url"],
                "content_source": record["content_source"],
                "opening_post_words": record["opening_post_words"],
                **classify_record(record),
            }
        )
    coded.sort(key=lambda row: (int(row["cohort_year"]), int(row["sample_order"])))
    write_csv(OUT / "coded-initial.csv", coded)

    audit_yes: set[int] = set()
    for year in COHORTS:
        launches = [
            row
            for row in coded
            if int(row["cohort_year"]) == year
            and row["initial_launch_eligibility"] == "launch"
        ]
        rng = random.Random(SEED + year + 99)
        audit_yes.update(
            int(row["topic_id"]) for row in rng.sample(launches, min(20, len(launches)))
        )
    queue: list[dict[str, Any]] = []
    content = {int(row["topic_id"]): row for row in records}
    for row in coded:
        topic_id = int(row["topic_id"])
        if row["initial_launch_eligibility"] == "launch" and topic_id not in audit_yes:
            continue
        queue.append(
            {
                **row,
                "audit_reason": (
                    "random_launch_audit"
                    if topic_id in audit_yes
                    else "all_nonlaunch_and_uncertain"
                ),
                "opening_post_text": content[topic_id]["opening_post_text"],
                "review_launch_eligibility": "",
                "review_project_type": "",
                "review_note": "",
            }
        )
    write_csv(OUT / "review-queue.csv", queue)
    print(
        json.dumps(
            {
                "coded": len(coded),
                "initial_eligibility": Counter(
                    row["initial_launch_eligibility"] for row in coded
                ),
                "review_queue": len(queue),
                "random_launch_audits": len(audit_yes),
            },
            indent=2,
            default=dict,
        )
    )


def run_finalize() -> None:
    initial = read_csv(OUT / "coded-initial.csv")
    review_queue = read_csv(OUT / "review-queue.csv")
    review_payload = json.loads(
        (OUT / "manual-review.json").read_text(encoding="utf-8")
    )
    reviews = {
        int(topic_id): values
        for topic_id, values in review_payload["topics"].items()
    }
    queued_ids = {int(row["topic_id"]) for row in review_queue}
    missing_reviews = sorted(queued_ids - set(reviews))
    if missing_reviews:
        raise RuntimeError(
            f"Manual review does not cover the full review queue: {missing_reviews}"
        )

    final: list[dict[str, Any]] = []
    for row in initial:
        topic_id = int(row["topic_id"])
        review = reviews.get(topic_id)
        eligibility = (
            review["launch_eligibility"]
            if review
            else row["initial_launch_eligibility"]
        )
        project_type = (
            review["project_type"] if review else row["initial_project_type"]
        )
        reason = review["review_note"] if review else row["initial_reason"]
        coding_agent_evidence = (
            review.get("coding_agent_evidence", row["coding_agent_evidence"])
            if review
            else row["coding_agent_evidence"]
        )
        final.append(
            {
                "topic_id": topic_id,
                "cohort_year": row["cohort_year"],
                "sample_order": row["sample_order"],
                "category_id": row["category_id"],
                "category_name": row["category_name"],
                "title": row["title"],
                "url": row["url"],
                "launch_eligibility": eligibility,
                "eligibility_reason": reason,
                "project_type": project_type,
                "linked_github_repository": row["linked_github_repository"],
                "coding_agent_evidence": coding_agent_evidence,
                "manual_reviewed": "yes" if review else "no",
                "initial_launch_eligibility": row["initial_launch_eligibility"],
                "initial_project_type": row["initial_project_type"],
            }
        )
    if len(final) != 200:
        raise RuntimeError(f"Expected 200 final codes, got {len(final)}")
    write_csv(OUT / "coded-final.csv", final)
    changes = sum(
        row["launch_eligibility"] != row["initial_launch_eligibility"]
        or row["project_type"] != row["initial_project_type"]
        for row in final
    )
    print(
        json.dumps(
            {
                "final_records": len(final),
                "manually_reviewed": sum(row["manual_reviewed"] == "yes" for row in final),
                "changed_by_review": changes,
                "eligibility": dict(
                    Counter(row["launch_eligibility"] for row in final)
                ),
            },
            indent=2,
        )
    )


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 1.0)
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return max(0.0, centre - margin), min(1.0, centre + margin)


def run_analyze() -> None:
    coded = read_csv(OUT / "coded-final.csv")
    manifest = json.loads((OUT / "sample-manifest.json").read_text(encoding="utf-8"))
    cohorts: dict[str, Any] = {}
    for year in COHORTS:
        rows = [row for row in coded if int(row["cohort_year"]) == year]
        counts = Counter(row["launch_eligibility"] for row in rows)
        launches = counts["launch"]
        population = int(manifest["cohorts"][str(year)]["population"])
        estimated_lower_count = 0.0
        estimated_upper_count = 0.0
        estimated_types: Counter[str] = Counter()
        for category_id_raw, stratum in manifest["cohorts"][str(year)]["strata"].items():
            category_id = int(category_id_raw)
            stratum_population = int(stratum["population"])
            stratum_rows = [
                row for row in rows if int(row["category_id"]) == category_id
            ]
            if not stratum_rows:
                estimated_upper_count += stratum_population
                continue
            stratum_sample = len(stratum_rows)
            weight = stratum_population / stratum_sample
            estimated_lower_count += weight * sum(
                row["launch_eligibility"] == "launch" for row in stratum_rows
            )
            estimated_upper_count += weight * sum(
                row["launch_eligibility"] in {"launch", "uncertain"}
                for row in stratum_rows
            )
            for row in stratum_rows:
                if row["launch_eligibility"] == "launch":
                    estimated_types[row["project_type"]] += weight
        lower_share = estimated_lower_count / population
        upper_share = estimated_upper_count / population
        wilson_low, wilson_high = wilson_interval(launches, len(rows))
        cohorts[str(year)] = {
            "sample": len(rows),
            "population_topics": population,
            "eligibility": dict(counts),
            "launch_share_partial_identification": {
                "lower": lower_share,
                "upper": upper_share,
            },
            "design_naive_confirmed_launch_share_wilson_95": {
                "lower": wilson_low,
                "upper": wilson_high,
                "note": "Treats uncertain as not confirmed and ignores small stratum-weight differences; shown only as a rough sampling-error check.",
            },
            "estimated_launch_count_bounds": {
                "lower": estimated_lower_count,
                "upper": estimated_upper_count,
            },
            "project_type_sample_counts_among_confirmed_launches": dict(
                Counter(
                    row["project_type"]
                    for row in rows
                    if row["launch_eligibility"] == "launch"
                )
            ),
            "estimated_project_type_counts_among_confirmed_launches": {
                key: round(value, 2) for key, value in estimated_types.items()
            },
            "explicit_coding_agent_disclosures_all_sampled_topics": sum(
                row["coding_agent_evidence"] == "confirmed_explicit_disclosure"
                for row in rows
            ),
            "explicit_coding_agent_disclosures_confirmed_launches": sum(
                row["coding_agent_evidence"] == "confirmed_explicit_disclosure"
                and row["launch_eligibility"] == "launch"
                for row in rows
            ),
        }

    pre = cohorts["2025"]["estimated_launch_count_bounds"]
    post = cohorts["2026"]["estimated_launch_count_bounds"]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cohorts": cohorts,
        "surge_robust_to_all_uncertain_assignments": post["lower"] > pre["upper"],
        "worst_case_launch_count_ratio": (
            post["lower"] / pre["upper"] if pre["upper"] else None
        ),
        "best_case_launch_count_ratio": (
            post["upper"] / pre["lower"] if pre["lower"] else None
        ),
        "scope": {
            "topic_opening_posts_only": True,
            "repository_quality_inspected": False,
            "traction_inspected": False,
            "ai_prevalence_estimated": False,
            "unknown_ai_cases_used_as_non_ai_control": False,
        },
    }
    (OUT / "launch-validation-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def run_validate() -> None:
    sample = read_csv(OUT / "sample.csv")
    opening = load_opening_posts()
    checks = {
        "sample_has_200_unique_topics": (
            len(sample) == 200 and len({row["topic_id"] for row in sample}) == 200
        ),
        "sample_has_100_per_cohort": (
            Counter(row["cohort_year"] for row in sample)
            == Counter({"2025": 100, "2026": 100})
        ),
        "opening_posts_complete": (
            len(opening) == 200
            and {int(row["topic_id"]) for row in opening}
            == {int(row["topic_id"]) for row in sample}
        ),
        "all_opening_posts_nonempty": all(
            str(row["opening_post_text"]).strip() for row in opening
        ),
        "no_replies_or_repositories_collected": all(
            "replies" not in row and "repository_content" not in row for row in opening
        ),
    }
    final_path = OUT / "coded-final.csv"
    if final_path.exists():
        final = read_csv(final_path)
        checks.update(
            {
                "final_codes_complete": len(final) == 200,
                "final_eligibility_valid": all(
                    row["launch_eligibility"]
                    in {"launch", "not_launch", "uncertain"}
                    for row in final
                ),
                "unknown_ai_not_labeled_non_ai": all(
                    row["coding_agent_evidence"]
                    in {"confirmed_explicit_disclosure", "unknown", "explicit_no"}
                    for row in final
                ),
            }
        )
    result = {"checks": checks, "passed": all(checks.values())}
    (OUT / "validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    commands = {
        "sample": run_sample,
        "topics": run_topics,
        "classify": run_initial_classification,
        "finalize": run_finalize,
        "analyze": run_analyze,
        "validate": run_validate,
    }
    if command not in commands:
        raise SystemExit(
            "Usage: collect_launch_validation.py "
            "{sample|topics|classify|finalize|analyze|validate}"
        )
    commands[command]()


if __name__ == "__main__":
    main()
