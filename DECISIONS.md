# Markdown experiment decisions

## Core decisions

- [Preserve dated evidence and create a new directory for every run](#preserve-evidence).
- [Separate experiment completion from answer correctness](#interpret-results).

## Details

### Preserve evidence

Keep September 4 captures unchanged and the repository private. Fresh runs save
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
  navigating unrelated research. Keep the substantive website recommendations in
  the existing Google Doc linked from the README.
