# Recovery status

The original research directory disappeared after the article was packaged.
This archive was rebuilt from two surviving sources:

1. the frozen `visualization-data.json` published with the article;
2. the original Codex task transcript, which retained the codebook, scripts,
   manual-review decisions and taxonomy review patches.

The recovered material is intentionally split into exact, reconstructed and
missing evidence. See `data/recovered/README.md` and
`data/recovered/recovery-manifest.json` before using it for corrections or new
claims.

Raw opening-post bodies are not included in the public archive. Their original
snapshots were not recoverable byte-for-byte, and republishing complete forum
posts would add copyright and privacy surface without improving the coding
ledger. Topic URLs are retained for source inspection.

The public files contain no forum author or username fields, author IDs, email
addresses, IP addresses, replies, repository contents or complete post bodies.
Review notes are short paraphrases of the coding decision, not excerpts from a
post.

The recovered codebook also preserves fields planned for later research.
Version 1 populated launch eligibility, project type and coding-agent evidence,
then added the 53-record integration taxonomy. It did not complete the planned
author, quality, traction or inter-rater-reliability work.

`scripts/collect_launch_validation.py` is retained as a methodological record.
It cannot run end to end without the missing census input, and its `topics`
command stores complete opening posts locally. Those paths are excluded by the
research directory's `.gitignore` and must not be published.

## Verify the recovered archive

From the repository root:

```sh
python3 -m unittest discover -s research/ha-project-launch-scout/tests -v
python3 research/ha-project-launch-scout/scripts/build_recovery_ledger.py \
  data/visualization-data.json
```

See `PUBLICATION-REVIEW.md` for the public-file decision, privacy checks and
remaining caveats.
