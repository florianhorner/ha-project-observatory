# Recovered research ledger

This directory restores the audit trail behind the published Home Assistant
Project Observatory dataset. It was reconstructed on 2026-08-17 after the
original local research directory was lost.

## What is exact

- Final labels, titles, URLs and weights for all 200 sampled topics come from
  the frozen publication snapshot with SHA-256
  `565257528fe0e541f84c547b05baf117e9adc95526aab696ca86e15c5494af10`.
- The 124 manual-review decisions and their notes were replayed from the
  original Codex task transcript.
- The 53 integration domain, connection-surface and scope assignments were
  checked against both the frozen publication snapshot and the recovered
  taxonomy review ledger.
- The seed, category populations, category allocations and weight formula were
  recovered from the original sampling implementation.

## What is reconstructed or missing

- `possible_stratum_category_ids` is inferred from each published weight. A
  2025 weight of `4.0` can mean either Scripts or Themes, so those rows remain
  explicitly ambiguous.
- The original raw category-listing files and opening-post snapshots were not
  preserved. Current forum pages may differ from their launch-date versions.
- Generated intermediate files that existed only on the lost local disk are
  not presented as recovered originals.
- The four Q1 2026 Theme posts received no sampled records. They had zero
  inclusion probability under the largest-remainder allocation.

## Files

- `sample-audit-ledger.csv`: all 200 sampled topics, final codes, weights,
  recovered review notes and integration codes.
- `integration-taxonomy.csv`: the 53 integration records extracted from that
  audit ledger.
- `sampling-design.json`: exact sampling strata, allocation and weighting
  rules.
- `recovery-manifest.json`: provenance, missing artifacts and checksums.

The linked forum topic remains the primary source for challenging a code. A
correction should name the topic ID, field, existing value, proposed value and
reason. Corrections belong in a new dataset version; this recovery does not
silently rewrite the frozen publication snapshot.

The public ledger contains topic titles and URLs, final codes, weights and short
paraphrased review reasons. It excludes author and username fields, complete
opening posts, replies, email and IP fields, repository contents, and the raw
collection cache. The missing raw snapshots mean the historical claim that 105
edited opening posts were reconstructed cannot be independently replayed from
this archive.
