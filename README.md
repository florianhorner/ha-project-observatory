# HA Project Observatory

An interactive data story about what people launched in the Home Assistant
Community's “Share your Projects” forum.

**Read the article:**
[florianhorner.github.io/ha-project-observatory](https://florianhorner.github.io/ha-project-observatory/)

## The finding

In two Q1 forum samples, projects built mainly on Home Assistant rose from one
of 20 classified integration launches in 2025 to nine of 33 in 2026.

That result is suggestive, not an ecosystem census. The 2025 baseline is one
project, the study has one reviewer, and the observed forum change may partly
reflect traffic, category use or posting culture.

The original question was whether AI coding tools had triggered a surge. The
public posts do not disclose enough about how most projects were made to test
that theory reliably.

## Evidence package

- `data/visualization-data.json` contains the frozen publication dataset.
- It includes 53 classified integration launches and 200 sampled forum topics.
- Every displayed project links back to its Home Assistant Community source.
- Weighted estimates and raw sample counts are labelled separately in the
  article.

The article records what projects claimed at launch. It does not measure
installs, reliability, maintenance or survival.

## Read locally

The published site is static HTML, CSS and JavaScript. No build step is needed.

```bash
git clone https://github.com/florianhorner/ha-project-observatory.git
cd ha-project-observatory
python3 -m http.server 8000
```

Then open <http://localhost:8000/>.

## Corrections

Classification challenges and factual corrections are welcome through
[GitHub issues](https://github.com/florianhorner/ha-project-observatory/issues).
Please name the affected topic and explain what you would classify differently.

## Impact measurement

GitHub stars, forks and issues measure evidence reuse, not article readership.
Channel-specific campaign links can preserve attribution, but this publication
does not currently include visitor analytics or interaction tracking.

## Publishing model

The repository mirrors the Smart Home Gazette setup: GitHub Pages serves the
prebuilt files from the root of `main`. The `.nojekyll` marker keeps the assets
untouched.
