<!-- Copyright (c) 2026 Christian Reitwiessner. Apache-2.0. Authors: Christian Reitwiessner. -->
# Dashboard maintenance

This repository tracks the optional STOC formalization experiment in
`cslib-community/complexitylib`, issue 2527. It does not host the Lean library.

- Update `stoc/status.json` after each substantive implementation/review handoff. Preserve the
  full main-result objective and list remaining gaps. A bounded review is not whole-paper approval.
  Pin evidence to a full source SHA and primary paper/review link; never infer coverage from CI.
- Update the counted source prefixes when adding implementation or supporting modules. Counts
  include comments/blanks, exclude tests/docs, and may overlap across papers. Keep port attribution.
- Append actual task measurements to `stoc/resources.json`, identifying provenance. Do not guess
  historical token usage; use null for unknown. User-assigned budgets are limits, not usage.
  Task wall times overlap and must not be presented as total project elapsed/CPU time.
- All new files credit Christian Reitwiessner, preserving original authors and mathematical sources.
  Write “STOC submission 1234”, never issue-style paper numbers.
- Run Python tests, JavaScript syntax checking and an offline build before publishing. The Actions
  workflow performs the authenticated current-head refresh and Pages deployment. Failure must leave
  the previous visible snapshot intact; no silent stale-to-current relabelling.
- The default upstream cache has its own Git object database. Offline `--upstream` access is read
  only. Never modify another agent's checkout, build outputs, indexes or shallow boundaries.
