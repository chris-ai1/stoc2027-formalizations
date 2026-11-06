# STOC 2027 formalization dashboard

A separate, source-grounded tracker for the optional Complexitylib formalization experiment.
Published at **https://chris-ai1.github.io/stoc2027-formalizations/**.
These are submissions, not confirmed acceptances. The dashboard does not change Complexitylib's website.

Search all 1,665 submissions by title, author, topic or ID. Tracked papers expose scoped coverage,
remaining claims, primary PDF links, independent review evidence, PR state and reported checks.
The theorem explorer indexes actual theorem/lemma declarations with immutable GitHub source-line
links and statement excerpts. Supporting lemmas are not classified as main results automatically.
Newer PR revisions do not inherit a previous whole-head review automatically.

## Updates

GitHub Actions refreshes and publishes hourly at minute 23, on pushes to `main`, and on manual
dispatch. The builder queries upstream PR heads/checks and counts/extracts the explicitly scoped
Lean files at those exact revisions. It fetches into its own disposable upstream Git repository;
it does not change upstream branches, source files or indexes. API/fetch failures fail the build,
leaving the last successfully published snapshot and its visible timestamp intact.

Mathematical coverage is deliberately **curated**, not inferred from CI or keywords:

- `stoc/catalogue.json`: public submission metadata, source and snapshot date. No screening scores
  or correctness judgements are imported. Untracked entries say **not assessed**, not “unformalized.”
- `stoc/status.json`: per-paper scope, remaining results, PR, exact review revision/evidence and
  counted source prefixes. Update this in the same handoff as a reviewed formalization milestone.
  Include native implementation/support modules when they belong to the counted scope. Shared
  files may appear in multiple scopes, so line counts are not an additive originality measure.
- `stoc/resources.json`: explicit project/per-paper budgets and measured task records. Set
  `project_budget.time_hours`, `project_budget.tokens`, or `paper_budgets["733"]` to numeric limits
  when assigned. `null` means **not set**, never unlimited approval. Record tokens from provider
  telemetry only; `null` means **unknown**, never zero. Include measurement provenance. Wall time
  is the sum of recorded task intervals, which can overlap and cover only part of a paper's effort.
  Do not substitute estimates for measured token usage. Historical records currently contain
  selected completed-task elapsed times; provider token totals were unavailable.

Paper and theorem views show budgets, usage and coverage of recorded measurements. No spending,
CPU time, or remaining-token guarantee is inferred. Agents/reviewers are not human/platform approval.

## Build and validate

Requires Python 3.12+, Git and authenticated GitHub CLI (`gh`). No Lean or npm installation is needed.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/stoc_status.py --github --output site
```

Open the generated site through a static-file viewer. `site/data.json` is also a complete downloadable
snapshot including source paths, revisions, theorem locators and measurements. For an offline build
against an existing **read-only** Complexitylib checkout with the recorded revisions available:

```sh
python3 scripts/stoc_status.py --upstream /path/to/complexitylib --output site
```

Offline snapshots are explicitly labelled; they do not imply current GitHub checks. Never use
`--github --upstream` against another worker's protected checkout: use the default independent cache.

To publish, enable GitHub Pages with **GitHub Actions** as its source. `.github/workflows/pages.yml`
builds the static artifact and deploys it with Pages/OIDC permissions. Failed scheduled updates are
visible in Actions; the site always shows the last successful snapshot time. Catalogue additions and
mathematical-status changes require source review; automated check refreshes cannot certify semantics.

## Credit

Copyright (c) 2026 Christian Reitwiessner. Apache-2.0.
Submission titles/authors and primary papers retain their original attribution. Kong's existing
formalization is explicitly distinguished from newly developed proofs. This dashboard is a catalogue
and evidence index; the linked Lean sources, primary papers and review records are authoritative.
