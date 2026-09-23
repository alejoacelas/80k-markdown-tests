# Test how AI tools receive 80k pages

Cloudflare's Markdown serving was enabled for 80000hours.org on September 4,
2026. This repository keeps the evidence and a small experiment you can rerun
when the website or Claude Code changes. It does not operate the website.

Give Claude Code 30 exact URL–prompt pairs, capture what its WebFetch tool
returns, then independently download the same URLs as Markdown for comparison.
The questions check summaries, headings, footnotes, truncation, redirects and
404s. You can run just one or two questions first.

## Run it

Requirements: Python 3.10+, curl with `%{json}` support (7.70+), and Claude Code
with a working login. There are no Python packages to install. Use your work
Claude account; `claude auth status` shows which account is active. Runs consume
Claude usage: one fresh session per task, four at a time by default. This repo
stores no credentials and needs no `.env`.

```sh
git clone https://github.com/alejoacelas/80k-markdown-tests.git
cd 80k-markdown-tests
claude auth status
python3 run.py --ids about-summ,notfound
```

The command prints its output directory under `runs/`. Open its `results.md`.
For all 30 tasks:

```sh
python3 run.py
```

Options: `--ids ai-h2,ai-fn10` selects tasks, `--jobs 1` runs sequentially,
`--timeout 300` allows five minutes per session, and `--model MODEL_ID` selects
a model instead of the account default. `--output PATH` names a new output
folder. Existing folders are refused, so a rerun cannot overwrite evidence.
Without `--output`, each run gets a unique timestamped directory.

The runner exposes only WebFetch to Claude, disables skills and configured MCP
servers, and omits user/project/local settings. It supplies only the capture hooks.
Managed organisation policies still apply. It checks that each captured call used
the exact requested URL and prompt. It downloads the reference after the Claude
session, without exposing that download to the model.

## Read the results

**“Captured” means the experiment ran, not that Claude answered correctly.**
The runner exits nonzero on a timeout, invalid session output, missing/extra
capture, changed input, or failed reference transfer. An HTTP error such as the
intentional 404 is recorded as evidence, not a failed transfer.

Each run contains:

- `manifest.json`: date, Claude Code version, requested model and exact tasks.
- `results.md` and `results.json`: capture status, reference HTTP status and
  content type, response lengths and comparison fields.
- One folder per task: `calls.jsonl` has the unabridged WebFetch hook payload;
  `response.txt` extracts its answer; `claude.json` records session results,
  actual model usage and usage information; `*.stderr` contains diagnostics.
- `reference.body`, `reference.headers` and `reference.json` in each task folder:
  curl's independent response, including redirects, status and timings.

For a heading or quotation question, compare `response.txt` with
`reference.body`. For a serving check, inspect the reference content type and
whether headings, author/date and final sections survived conversion. A smaller
response does not establish a faithful conversion. The script does not grade
factual correctness or infer that missing text proves truncation.

The reference request prefers `text/markdown` and uses a Claude-style User-Agent.
It is **not a capture of WebFetch's internal input**: request headers, caches or
page changes can produce differences. The truncation-marker field searches the
returned answer, not the hidden input. Exact response/reference equality is a
literal comparison, not a quality score.

The second column in `tasks.tsv` describes the September 4 page size or condition;
it is a historical label. Current measured sizes are in `results.json`.

## What is worth keeping from September 4?

[The results](evidence/2026-09-04/results.md) document improved access to late
sections of the AI problem profile, but missing headings/bylines and continued
truncation of longer pages. These observations used **Claude Code 2.1.260**;
they are not guarantees about current Claude, Cowork, or other AI tools.

The [web-team report](https://docs.google.com/document/d/155zZn35tDBjrqRUghbpqdCT0LlpnqhNSXW6X3qTZ5VU/edit)
contains the findings and proposed theme changes or custom WordPress endpoint.
Those proposals are not implementations in this repository. The
[initial proposal](https://docs.google.com/document/d/1nP-gCaCpXBPRdBfggW6bhts5vjGI6kY-YClVgR_vtHs/edit)
provides the original motivation.

`evidence/2026-09-04/` preserves the exact prompts, captured calls and downloaded
reference pages from the
[original private experiment](https://github.com/alejoacelas/2026-09-webfetch-prompt-tests/tree/d5ae043/run5).
Fresh runs are ignored by Git. Keep this repository private.

## Files and checks

`run.py` runs the experiment, downloads references and writes the comparison.
`capture.py` saves hook payloads. `tasks.tsv` holds all 30 prompts. There is no
service, deployment, plugin or separate analysis command to maintain.

```sh
python3 -m unittest -v test_run.py
```

The offline tests cover payload preservation, task validation, overwrite
protection, missing captures and timeouts. Live validation is recorded below.

### Validation on September 23, 2026

All 30 tasks completed on Claude Code 2.1.280 with zero runner errors. The
captured sessions reported `claude-opus-5-5` and, where used by WebFetch,
`claude-haiku-4-5-20251001`. Independent reference downloads returned 28 Markdown
responses, the plain-text llms.txt, and the expected HTML 404. See the
[saved measurements](evidence/2026-09-23-results.json). This checks execution and
evidence capture; it does not certify all 30 answers as correct. The five offline
checks passed, and every historical evidence file matches the original bytes.
