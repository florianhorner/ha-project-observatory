# Launch-validation method

> Recovery note (2026-08-17): this method record was recovered from the original
> task transcript. The raw category listings and opening-post snapshots are
> missing, so the 105 edited-post reconstructions described below cannot be
> independently replayed from this archive. The counts are preserved as a
> historical method record, not presented as a new verification.

Run on 2026-07-26. This is the bounded gate authorized after the metadata
census. It does not inspect repositories, replies, quality, or traction.

## Question

Does the Q1 2026 increase in project-category topics represent more actual
project launches, or merely more questions, support posts, ideas, and updates?

## Sample

The source frame is the exact project-topic census. Two independent samples
were drawn:

- 100 of 416 Q1 2025 topics;
- 100 of 835 Q1 2026 topics.

Sampling was proportional by current forum category using largest-remainder
allocation and fixed seed `20260726`.

| Category | 2025 population | 2025 sample | 2026 population | 2026 sample |
| --- | ---: | ---: | ---: | ---: |
| Share your Projects parent | 208 | 50 | 360 | 43 |
| Custom Integrations | 102 | 24 | 355 | 43 |
| Dashboards & Frontend | 78 | 19 | 106 | 13 |
| Scripts | 24 | 6 | 10 | 1 |
| Themes | 4 | 1 | 4 | 0 |

The four unsampled 2026 theme topics are treated as entirely unknown in the
upper/lower population bounds, rather than silently assumed to resemble another
stratum.

## Original-post recovery

Only the opening post was collected. For each edited opening post, revision 2's
previous column was used to reconstruct version 1. All 200 posts were
retrieved; 105 were edited and all 105 original versions were reconstructed
without fallback to current content.

No replies or repository contents were opened.

## Eligibility coding

The frozen codebook defines:

- `launch`: usable or reproducible project, integration, frontend component,
  automation/configuration, add-on/tool, hardware build, or system build;
- `not_launch`: support question, solution request, idea, pre-release interest
  check, third-party reshare, or update whose original launch predates the
  topic;
- `uncertain`: the original opening post does not support a defensible binary
  decision.

A deterministic ruleset produced a triage pass. Every `not_launch` and
`uncertain` result, 40 randomly selected `launch` results, and obvious
support/update titles missed by the rules were manually reviewed. In total 124
of 200 posts received direct manual review. Review changed 52 eligibility calls
and 53 type calls; 17 records changed both. This confirms that the ruleset was
useful for triage but not reliable enough to serve as the final coder.

This was a single-reviewer gate, not independent double coding. Publication
quality would require a blinded second coder or a transparent community audit
of the coding sheet.

## Estimates

Population estimates use stratum weights, not an unweighted expansion. For
ambiguous posts:

- lower bound treats every `uncertain` as not a launch;
- upper bound treats every `uncertain` as a launch.

These are ambiguity bounds, not confidence intervals. A rough Wilson interval
is retained only as a sampling-error check and explicitly ignores the small
weight differences. With 100 topics per cohort and observed launch shares near
85–88%, the approximate 95% margin is about 7 percentage points. The sample can
validate a large count increase but cannot support subtle differences in launch
share or small project-type cells.

## Coding-agent evidence

Only explicit statements that a coding agent materially helped create code or
configuration are `confirmed`. AI functionality is not development evidence.
All other cases are `unknown`.

Disclosure sensitivity is unknown. Therefore public disclosures are only an
ascertainment floor. `unknown` is not a non-AI control group, and no AI-use
prevalence or AI-versus-non-AI outcome comparison is produced.
