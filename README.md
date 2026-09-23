# Serving 80k pages as Markdown to AI tools

**The Cloudflare change is deployed and working. Further improvements are optional,
with Rachel to judge their priority against her AI SEO work and Valerie available
to help.** The main benefit demonstrated was that Claude could read more of an
article before its input was cut off. We did not establish an improvement in AI
search rankings or ordinary summary quality.

## What happened and where we left it

On September 4, 2026, Alejo proposed serving Markdown to tools that request it,
so navigation and other page furniture would leave more room for article text.
Valerie tested Cloudflare's Markdown for Agents setting, then
[enabled it on all pages](https://80000hours.slack.com/archives/C0BHALFP9V4/p1788537690534279).
Alejo [confirmed the change worked](https://80000hours.slack.com/archives/C0BHALFP9V4/p1788541706054849)
and investigated the remaining conversion problems.

Valerie closed the discussion with:

> “And after this thread, it's already ~good enough.”

She [left prioritisation with Rachel](https://80000hours.slack.com/archives/C0BHALFP9V4/p1788549901641709),
who was following AI SEO, rather than asking for another implementation. This repo
contains the tests and evidence; Cloudflare serves the live Markdown without
these scripts running. No custom WordPress endpoint was built here.

## What the tests showed

The September 4 experiment made 30 captured WebFetch calls using **Claude Code
2.1.260**. Markdown-preferring requests received Markdown; browser requests still
received HTML. Claude still returned a model-generated answer, rather than passing
the page verbatim to the calling agent.

These are the most useful findings from the [full results](evidence/2026-09-04/results.md):

| Finding | Concrete evidence | Consequence |
|---|---|---|
| More article text fits | The AI problem profile was 276,269 characters as HTML and 123,780 as Markdown. Its body ended before the observed 100,000-character cutoff; later footnotes did not. Claude correctly quoted the acknowledgements and a late objection reply. | The configuration change delivered a useful improvement in access to late sections. |
| Some important text disappears | Cloudflare removed article titles, bylines and dates inside `<header>`. Listing-item titles disappeared too; Claude invented 3 of the first 5 titles it gave for `/latest/`. | If we improve conversion, restore these fields first. |
| Long pages still exceed the input budget | Loss of control was about 168,000 Markdown characters; the Shulman transcript 274,000. Claude once stitched together unrelated sentences as an answer about an unseen section. | Markdown alone does not make long pages fully readable; verify quotations against the source. |
| Repeated navigation consumes space | The Shulman transcript included its contents list twice, using 42,000 characters. Hidden CTA variants also survived conversion. | Removing duplication would leave more room for the article. |
| Search and discovery files are oversized | `/?s=alignment` returned 815,570 Markdown characters because it rendered full posts. `llms.txt` remained 870,361 characters. | Excerpts or smaller, curated indexes are possible follow-ups if these routes matter for AI discovery. |

Two excerpts capture the practical lessons:

> “Cloudflare strips `<header>`, and 80k's templates put titles, bylines and dates there.”
>
> “The summarizer is not reliable about what it did not see.”

Both are from the [September 4 findings](evidence/2026-09-04/results.md#findings).
The 100,000-character limit describes that tested client version. Cowork,
claude.ai's server-side fetcher and search-result snippets were not directly
verified; the Slack discussion's broader expectations should not be read as
measurements of those tools.

### September 23 check

The cleaned-up runner completed all 30 tasks on Claude Code **2.1.280**, with no
runner errors. Independent downloads returned 28 Markdown responses, the
plain-text `llms.txt`, and the expected HTML 404. A separate rerun also completed,
and all five offline checks passed. The
[saved measurements](evidence/2026-09-23-results.json) confirm that the experiment
runs and Markdown responses are still available; we did not manually regrade all
30 answers or re-establish the earlier truncation limit.

## Useful next steps, if Rachel prioritises this

1. **Restore titles, bylines and dates.** The existing investigation proposes
   changing the article title block from `<header>` to `<div class="entry-header">`,
   with equivalent changes for listing-item titles. Update the two CSS rules that
   target `.post header` so spacing remains intact. Check a post, page, problem
   profile, career review and podcast episode on staging.
2. **Remove duplicate navigation from the Markdown.** The proposed first step is
   to make the mobile contents overlay a `<nav>` while preserving its classes and
   IDs. The September 4 converter stripped `<nav>`. The same approach could remove
   the topic-filter navigation. Recheck the converted text after deployment and
   cache purges.
3. **Consider a custom endpoint only if more control is worth maintaining it.**
   Alejo's report preferred this longer term: WordPress could render just the
   article, retaining metadata and omitting repeated widgets. Its proposed `/md/`
   path and Cloudflare rewrite would need implementation and testing, including
   cache separation, cache invalidation and protection of unpublished content.
   It would introduce a second rendering path to maintain.

The [implementation report](https://docs.google.com/document/d/155zZn35tDBjrqRUghbpqdCT0LlpnqhNSXW6X3qTZ5VU/edit)
contains the detailed plans. It estimated about three engineer-hours for the
first four theme fixes, plus an hour of QA; these were planning estimates, not
completed work. For pages still too long after cleanup, section-specific URLs
are another option. Prioritise based on the pages and AI uses Rachel cares about,
then check their titles, metadata and final sections before and after a change.

## What the small experiment contains

[Tasks](tasks.tsv) are URL–prompt pairs. For example, the career-capital test asks:

> “Quote footnote 12 from the 'Notes and references' section in full, verbatim.”

The AI profile test asks:

> “Quote the 'Acknowledgements' section verbatim. If there is no such section in the content you received, say NOT PRESENT.”

[run.py](run.py) starts a fresh Claude session for each task, downloads a reference
page afterwards, and writes the comparison. [capture.py](capture.py) saves the
exact WebFetch request and response. The original September 4 prompts, captures
and reference pages are preserved unchanged under `evidence/2026-09-04/`.
Keep this employer repository private.

**“Captured” means the experiment completed, not that the answer is correct.**
For a quotation or heading test, compare the saved `response.txt` with
`reference.body`. Curl's reference is an independent download, not WebFetch's
hidden input; headers, caches or page changes can produce differences. Checking
for a truncation marker in the answer does not prove what the hidden input held.

Each run's `results.md` is the readable table; `results.json` contains errors and
measurements. `manifest.json` records the client version and tasks. Task folders
contain the raw `calls.jsonl`, `claude.json` with model usage, extracted answer,
reference body/headers/HTTP metadata, and error logs. The runner reports timeouts,
missing or extra captures, altered prompts and failed downloads. The deliberate
HTTP 404 is evidence, not a runner failure. Fresh runs are ignored by Git.

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


To check the runner without making model calls:

```sh
python3 -m unittest -v test_run.py
```

These checks cover capture preservation, task validation, refusal to overwrite
previous results, missing captures and timeouts. The second column in `tasks.tsv`
is a historical September 4 size/condition label; use each new run's measured
sizes when assessing current behaviour.
