# Publication dataset

`visualization-data.json` is the frozen data snapshot used by the published
interactive article.

## Contents

- `integrations`: 53 classified integration launch records.
- `aiTopics`: 200 sampled forum topics used for the disclosure check.
- `claims`: numeric claims rendered in the article.
- `labels`: display names for coded domains, connection surfaces and scope.
- `sources`: provenance pointers for the generated snapshot.

Each integration record includes its source topic URL, year, editorial domain,
connection surface, scope, GitHub-link detection and sample weight.

## Important limits

- A missing coding-agent disclosure means **unknown**, not human-only work.
- The coding scheme does not separate official core integrations from custom or
  HACS components.
- Protocol names were checked at title and target level; absence there does not
  prove that no Matter, Thread, Zigbee or Z-Wave work occurred.
- The study records launch claims, not installs, quality, maintenance or
  longevity.
- Section weights estimate the sampled forum mix and are not raw counts.

The Home Assistant Community topics linked in the dataset remain the primary
sources for auditing individual classifications.
