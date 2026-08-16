# Frozen Scout Codebook

Frozen before opening the selected topic bodies. Any later revision must be
versioned and applied to every observation, not only ambiguous records.

This file preserves the full planned codebook. Version 1 populated launch
eligibility, project type and coding-agent evidence, then added the 53-record
integration taxonomy. First-time-author, quality, traction and inter-rater
reliability work remained uncollected or incomplete and is not in the recovered
ledger.

## Population

Include a topic when its opening post presents a usable Home Assistant-related
project, integration, dashboard/frontend component, theme, script, add-on,
hardware build, or tool with enough material for another person to inspect,
install, reproduce, or use.

Exclude:

- Questions seeking a solution or asking whether something exists.
- Ideas, requests, and proposals without a usable artifact or reproducible build.
- Support-only threads and configuration troubleshooting.
- Updates or announcements whose original project launch predates the topic.
- WIP/tester requests without code, configuration, build instructions, or a
  demonstrable artifact at the opening-post date.

The forum topic creation timestamp is the launch date for this study. It is not
claimed to be the repository's first release date.

## Project type

Assign one primary type:

1. Custom integration or device bridge
2. Dashboard, card, theme, or frontend extension
3. Automation, blueprint, script, or configuration package
4. Add-on, application, developer, or operations tool
5. Hardware or physical build
6. Tutorial or reproducible system build
7. Other usable project

Record secondary domains separately: energy, climate, security, media/voice,
presence, health, transport, gardening, infrastructure, developer tooling,
dashboard/UI, and other.

## First-time project author

`yes` means no earlier observable topic by the opening-post author exists in the
parent Share your Projects category or its four subcategories. This is not a
claim that the person is new to software development or Home Assistant.

## Coding-agent evidence

- `confirmed`: the author or linked repository explicitly says a coding agent,
  LLM, or generative-AI tool wrote, generated, or materially assisted the code.
- `unknown`: no explicit statement was found.
- `explicit_no`: the author explicitly says no such tool was used.

AI-related functionality does not count as coding-agent evidence. Writing style,
code style, commit shape, repository age, and apparent polish are never evidence.

Public disclosure has unknown sensitivity: people may use coding agents heavily
without mentioning them. Therefore `unknown` is not a non-AI control group, the
observed disclosure rate is only a lower bound, and this study will not estimate
AI-use prevalence from public artifacts alone.

## Quality signals

Each signal is coded `yes`, `no`, or `not_applicable/unknown`; no combined public
quality score is created.

- Public artifact or reproducible configuration is reachable.
- Installation or reproduction instructions are present.
- The project describes its purpose and supported scope.
- License is declared when a software repository is provided.
- Versioned release or stable installation reference exists.
- Repository shows activity after launch.
- Tests or automated checks are visible.
- Opening post or documentation states meaningful limitations.

## Traction

Primary measures:

- Non-author replies within 30 and 90 days.
- Unique non-author participants within 30 and 90 days.

Secondary measures:

- Opening-post likes at the collection snapshot.
- Current views and views per age-day.
- Repository stars, forks, and post-launch activity at the collection snapshot.

These measure attention and discussion, not installations or active adoption.

## Ambiguity and recoding

- Record a reason for every exclusion and every `unknown` decision.
- A blinded 20% subset is coded again after shuffling.
- Gate A requires Cohen's kappa >= 0.70 on launch eligibility, primary type,
  coding-agent evidence, and the quality indicators used in analysis.

The blinded recode and Gate A were planned but not completed for the published
version. The final dataset has one classifier.
