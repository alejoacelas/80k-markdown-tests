# Markdown experiment decisions

## Core decisions

- [Preserve dated evidence and create a new directory for every run](#preserve-evidence).
- [Separate experiment completion from answer correctness](#interpret-results).

## Details

### Preserve evidence

Keep September 4 captures unchanged. Alejo approved making this repository public
on September 23, 2026. Fresh runs save
separate outputs and independently download reference pages after WebFetch. This
allows comparison without replacing the evidence behind the original report.
Implemented in [7b76c5e](https://github.com/alejoacelas/80k-markdown-tests/commit/7b76c5e).

### Interpret results

A completed capture does not establish a correct answer. Curl's reference is not
WebFetch's hidden input, and a historical client limit is not a guarantee about a
newer client. Keep the exact tool response and observed client version; compare
quotations and headings against source text when drawing conclusions.

## Decision log

- 2026-09-23: Extract the Markdown experiment into a small private repository with
  one runner and the original evidence, so the web team can reproduce it without
  navigating unrelated research.

- 2026-09-23: Make the README sufficient for Valerie to understand the deployment,
  evidence, remaining problems and optional next steps. Include the findings and
  excerpts directly, with run instructions last; link the Google Doc for detailed
  implementation plans. Preserve the Slack decision that Rachel judges priority
  and Valerie helps as needed. See [ea48cf5](https://github.com/alejoacelas/80k-markdown-tests/commit/ea48cf5).

- 2026-09-23: Publish this repository at Alejo’s explicit request. Checked tracked
  files and Git history for credentials before changing visibility. Linked internal
  resources retain their existing permissions.
