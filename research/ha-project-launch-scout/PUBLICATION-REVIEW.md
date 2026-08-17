# Publication review

Review date: 2026-08-17

Status: **ready to publish with the caveats below**. No figure in the frozen
article dataset changed during recovery or review.

## Public files

The recovered codebook, method note, sampling design, 200-record audit ledger,
53-record integration taxonomy, short manual-review notes, recovery builder and
tests are suitable for the public repository. They let a reader inspect the
sample, codes, weights and reconstruction boundaries.

The public records contain forum topic IDs, titles and URLs. They do not contain
forum author or username fields, complete opening posts, replies, email
addresses, IP addresses, repository contents or local machine paths. Review
notes are short paraphrases written for the coding audit.

## Files kept local

The missing original category listings and opening-post snapshots are not
represented by current forum downloads. The collector can create full local
post caches and working files under `data/census`, `data/raw` and
`data/launch-validation`; the research `.gitignore` blocks those paths while
retaining the recovered `manual-review.json`.

## Verification

- The frozen publication file still has SHA-256
  `565257528fe0e541f84c547b05baf117e9adc95526aab696ca86e15c5494af10`.
- The recovered ledger contains 200 unique topics, 100 per cohort, 124 recovered
  manual decisions and 53 integration records.
- The weighted integration inputs remain 84.82 for 2025 and 272.67 for 2026,
  before rounding to the published whole-number estimates.
- The archive's generated-file checksums reproduce.
- A public-repository credential scan found no secrets. Three medium findings
  were reviewed as false positives: the documented localhost preview URL is not
  private infrastructure, and a sampling probability plus the Wilson-interval
  constant are not payment-card data.

## Required caveats

- The raw category listings and opening-post snapshots are missing. The claim
  that 105 edited posts were reconstructed is preserved from the historical
  method record but cannot be independently replayed from this archive.
- Some 2025 records with weight 4.0 cannot be assigned uniquely to Scripts or
  Themes; the ledger marks both possible strata.
- The four Q1 2026 Theme topics had zero inclusion probability under the
  recovered allocation.
- Version 1 used one classifier. The planned blinded recode and reliability gate
  were not completed.
- The ledger supports inspection and correction of launch classifications. It
  does not add evidence about installs, quality, maintenance, longevity or
  actual AI-tool prevalence.
- The repository has no license file. The archive can be inspected publicly,
  but reuse terms remain unclear until the owner chooses a license.
