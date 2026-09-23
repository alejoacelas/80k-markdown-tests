# Run 5: 80000hours.org after Cloudflare's Markdown for Agents was switched on

Valerie enabled Cloudflare's [Markdown for Agents](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/) on all 80000hours.org pages on 4 September 2026 ([Slack thread](https://80000hours.slack.com/archives/C0BHALFP9V4/p1788525505282749)). This run checks what Claude Code's WebFetch now receives and returns. Claude Code 2.1.260, 4 September 2026, 30 hook-captured calls (`calls.jsonl`), each from a fresh headless `claude -p` session allowed only WebFetch. `ref-cu/` holds what the server returned to curl with WebFetch's exact headers; `analyze.py` prints the matrix.

## What WebFetch sends

Captured live by fetching `https://httpbin.org/headers` with WebFetch, which echoed the request:

```
Accept: text/markdown, text/html, */*
Accept-Encoding: gzip, compress, deflate, br
User-Agent: Claude-User (claude-code/2.1.260; +https://support.anthropic.com/)
```

Cloudflare serves markdown only when `text/markdown` outranks `text/html` in the Accept header. Tested on `/about/`: `text/markdown` and `text/markdown, text/html, */*` return markdown; `text/html, text/markdown`, `text/markdown;q=0.5, text/html`, `*/*` and browser Accept headers return HTML. Codex's fetch sends `text/markdown,text/plain,*/*` (string in the 0.153.0 binary), so it qualifies too.

## What the server now returns

| Page | HTML chars | Markdown chars | Markdown tokens | Fits under 100k cutoff |
|---|---|---|---|---|
| /about/ | 141,260 | 25,329 | 6,290 | yes |
| / (home) | 282,536 | 38,043 | 9,450 | yes |
| /career-guide/career-capital/ | 188,960 | 62,198 | 15,434 | yes |
| /career-reviews/ai-safety-researcher/ | — | 89,924 | 22,299 | yes |
| /latest/ | — | 80,308 | 19,922 | yes |
| /problem-profiles/artificial-intelligence/ | 276,269 | 123,780 | 30,657 | body yes, footnotes cut |
| /podcast/episodes/ | — | 125,828 | 31,080 | no |
| /problem-profiles/loss-of-control/ | — | 167,733 | 41,568 | no, cut in the objections |
| /podcast/episodes/carl-shulman-economy-agi/ | — | 273,537 | 67,740 | no |
| /?s=alignment | — | 815,570 | 202,354 | no |
| /llms.txt | 870,361 (text/plain) | unchanged | — | no |
| 404 page | 93,613 | served as HTML | — | WebFetch returns "HTTP 404", body not fetched |

Browsers still get HTML: the markdown variant is cached separately (`vary: Accept-Encoding, accept`, `cf-cache-status: HIT` on both). Same-host redirects (`/about` → `/about/`, `http://` → `https://`, the old `/risks-from-power-seeking-ai/` slug) are followed silently and end in markdown.

## What WebFetch does with it

Still a model answer, never the page: 80000hours.org is not on the compiled-in pass-through list (zero occurrences of "80000hours" in the 2.1.260 binary), so every call went to the summarizer. The `bytes` field of each tool response equals the markdown size, confirming the summarizer received the markdown.

| Task | Page | Prompt (short) | Result | Verdict |
|---|---|---|---|---|
| about-summ | /about/ | summarize | 417-char summary | as in run 4 (431) |
| cc-trunc | career-capital 62k | ends with truncation marker? | NO; quoted author bio from the JSON-LD tail | correct |
| cc-fn12 | career-capital | quote footnote 12 | full footnote, verbatim | correct |
| ai-h2 | AI profile 123k | list every H2 | 7 H2s incl. What's next, Learn more, Acknowledgements | correct; run 2 (HTML) was cut in the 3rd objection |
| ai-ack | AI profile | quote Acknowledgements (at 97.9k) | verbatim | correct |
| ai-objx | AI profile | quote reply to "isn't issue X bigger?" (91.8k) | verbatim | correct |
| ai-fn1 | AI profile | quote footnote 1 (98.5k) | verbatim | correct |
| ai-fn10 | AI profile | quote footnote 10 (106.6k) | NOT PRESENT | correct |
| ai-trunc | AI profile | marker present? | YES, last words match the 100k cut | correct |
| loc-trunc | loss-of-control 166k | marker present? | **NO**, then quoted the mid-sentence cut | wrong |
| loc-trunc2 | same prompt, new session | | YES | correct |
| loc-trunc3 | quote final 40 words | | "appears to be truncated" | correct |
| loc-trunc4 | TRUNCATED/COMPLETE first | | TRUNCATED | correct |
| loc-h2 | loss-of-control | list every H2 | 17 items copied from the TOC, incl. H3/H4s and sections past the cut | wrong |
| loc-unplug | loss-of-control | quote reply to "unplug" objection (113k, past cut) | **Fabricated**: two sentences from positions 51k and 63k presented as the reply | wrong |
| loc-sandbox | loss-of-control | quote reply to "sandbox" objection (115k) | NOT PRESENT, explained the cut | correct |
| loc-help | loss-of-control | list "How you can help" (119k) | NOT PRESENT | correct |
| loc-learnmore | loss-of-control | list "Learn more" (123k) | NOT PRESENT | correct |
| pod-trunc | Shulman episode 273k | marker present? | YES | correct |
| podeps-trunc | /podcast/episodes/ 125k | marker present? | YES | correct |
| llms-txt | llms.txt | quote last 20 words | refused: content truncated | as in run 4 |
| latest-summ | /latest/ | first five titles | 3 of 5 not on the page | **fabricated** |
| search-md | /?s=alignment | first five result titles | 2 of 5 not on the page | **fabricated** |
| about-first | /about/ | first 60 words | front matter, then "Search for:" | shows what the summarizer sees first |
| latest-first | /latest/ | first 40 words | "Search for: ##### Explore our archive by topic..." then ~2,100 words of topic taxonomy | shows the sidebar survives |
| notfound | 404 URL | summarize | "HTTP 404 Not Found. The response body was not retrieved." | correct |
| noslash, oldslug, http-plain | redirects | summarize | markdown of the target, 25,329 / 167,733 bytes | followed silently |

## Findings

1. **The toggle works and does what the brief predicted.** Article pages arrive as markdown at roughly one fifth of the HTML size, browsers are unaffected, and the summarizer's 100,000-character budget now holds the whole body of the AI problem profile (body ends at 94k, notes at 98k). Questions about its last sections, which run 2 could not answer from HTML, now come back verbatim and correct.

2. **Long pages are still cut.** Loss of control (167k), every podcast transcript (the Shulman episode is 273k), the episodes index (125k) and the site search page (815k) exceed the cutoff as markdown. Anything after 100,000 characters is invisible to the agent.

3. **Cloudflare strips `<header>`, and 80k's templates put titles, bylines and dates there.** The article H1, "By Zershaaneh Qureshi · Published February 2026" and the equivalent on every page tested are gone from the markdown; only the meta-tag title survives in the front matter. On listing pages (`/latest/`, search results) each item's `<h2 class="entry-title">` sits inside `<header>`, so all item titles vanish and the summarizer invents them: 3 of 5 titles it listed for `/latest/` and 2 of 5 for the search page do not exist. Agents cannot cite author or date from these pages.

4. **Chrome that survives conversion.** Per page: a "Search for:" line; the table of contents twice ("On this page" plus "Table of Contents", 1.7k chars on /about/, 11k on loss of control, 42k on the Shulman transcript, whose chapter list appears twice); the one-on-one advice call-to-action block repeated three to five times on problem profiles; a JSON-LD schema block of 2 to 6k chars at the end; on `/latest/` a 14k-char topic-filter sidebar before the first item. On the Shulman episode the duplicated TOC alone eats 42% of the budget.

5. **Site search renders full articles.** `/?s=alignment` is 815k of markdown because the WordPress search template outputs entire posts. Any agent that fetches a site search URL gets one article and a truncation marker.

6. **The summarizer is not reliable about what it did not see.** With five parallel sessions on the same cut page it answered the truncation check wrong once in four tries, listed headings past the cut from the TOC as if present, and once stitched sentences from two other sections into a "reply" for a section it never received. Asking it to say NOT PRESENT worked in four of five cases; the failure is not detectable from the answer alone.

7. **404s are safe.** WebFetch returns the status without a body, so the 93k-character 404 page is never summarized.

## Not tested

- Cowork and the claude.ai server-side fetcher: no API key was available to observe their request headers. Cowork runs the Claude Code harness so the same code likely applies; the server-side `web_fetch` tool may send a different Accept header.
- WebSearch result snippets (fetched server-side by Anthropic): whether they now come from markdown is unobservable from the client.
- Whether the cleaner input improves ordinary summary quality, as opposed to reach: summaries of /about/ and the home page look like run 4's.

## Recommended follow-ups for the web team

- Move the article H1, byline and date out of `<header>`, or give `<header>` a different element, so Cloudflare keeps them; same for `entry-title` on listing pages.
- Emit the table of contents once, and drop the "Search for:" input, the repeated advice CTA and the JSON-LD from the markdown variant if Cloudflare allows a `cssSelector`, or via a WordPress-side markdown response.
- Return a short results list, not full posts, from `/?s=`.
- For pages over 100,000 characters as markdown (loss of control, transcripts), consider per-section URLs or a curated `llms-full.txt` under 100k per file.
