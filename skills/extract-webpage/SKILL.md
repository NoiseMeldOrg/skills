---
name: extract-webpage
description: >
  Extract web pages into structured Markdown. Use when the user provides a URL and wants
  it converted to Markdown, says "extract this page," "scrape this site," "grab that article,"
  or drops a URL to a blog post, article, documentation page, or informational site. Also
  triggers when the user mentions a website they want archived, saved for reference, or
  converted to a readable document. For YouTube videos use extract-transcript instead.
  For PDFs use extract-book or extract-study.
---

# Extract Web Page to Structured Markdown

Convert web pages into clean, structured Markdown with metadata headers and boilerplate removed. The bundled Python script uses trafilatura for content extraction -- it strips navigation, ads, footers, and sidebars automatically, producing the article content as Markdown.

The script walks a cascade of fetchers and uses the first one that returns enough content: `trafilatura.fetch_url` (fast static fetch via the requests library) -> subprocess `curl` (bypasses Cloudflare's TLS-fingerprint block on requests) -> headless Chromium with `domcontentloaded` (handles JS-rendered SPAs without waiting for analytics or websocket connections to settle) -> headless Chromium with `networkidle` (last-resort wait for sites that need it). Most pages succeed at step 1 or 2; Playwright is invoked only for genuinely JS-only sites. Override the cascade with `--fetcher {auto,requests,curl,playwright}`.

For SPAs whose content sits in generic `<div>` containers (no `<main>` or `<article>` semantic tags), trafilatura sometimes returns plenty of words but strips all the structure -- a wall of paragraphs with no headings or lists. When that happens, the script automatically falls back to Mozilla's Readability (via `readability-lxml`), which scores by text density rather than tag semantics and preserves the heading hierarchy. The fallback fires when trafilatura returns zero headings on a non-trivial page; it announces itself with a `(using Readability fallback ...)` line on stderr.

Handles two modes:
- **Single page** (default): one URL, one document
- **Site crawl** (`--crawl`): discovers pages via sitemap or link following, extracts each, combines into one document with a table of contents

## When to Use

- User provides a URL and wants it in Markdown
- User says "extract this page," "scrape this site," "grab that article"
- User wants to archive a web page for reference
- User wants to save documentation or a blog post as Markdown
- User drops a URL to an article, research summary, or informational page

Do NOT use for:
- YouTube videos (use `extract-transcript`)
- PDF files (use `extract-book` or `extract-study`)
- Pages behind authentication (the script can only fetch public pages)

## Setup

The script requires `trafilatura`, plus `playwright` for the JS-rendering fallback and `readability-lxml`+`markdownify` for the structure-recovery fallback. Pick **one** of the two install paths below. The skill is invoked from arbitrary working directories (often outside any Python project), so do **not** assume a project-local `.venv/` exists at the cwd — that's the most common reason this skill silently fails.

### Path A — skill-local venv (recommended, portable)

Install everything into a dedicated venv that lives inside the skill folder itself. The skill is then independent of whatever directory the user is in when invoking it.

```bash
python3 -m venv {SKILL_DIR}/.venv \
  && {SKILL_DIR}/.venv/bin/pip install --quiet trafilatura playwright readability-lxml markdownify \
  && {SKILL_DIR}/.venv/bin/playwright install chromium
```

After that, every invocation calls `{SKILL_DIR}/.venv/bin/python {SKILL_DIR}/scripts/extract_webpage.py …` directly (no `source activate` needed — the venv's python knows its own context).

### Path B — user-site install (quick start, no venv)

For machines where adding a venv per skill feels heavy, install into the user's site-packages instead. On macOS with the system Python 3.12+, PEP 668 blocks a plain `pip install --user`; pass `--break-system-packages` (safe — it only writes to `~/Library/Python/3.x/lib/python/site-packages/`, never to the system Python).

```bash
pip3 install --user --break-system-packages trafilatura playwright readability-lxml markdownify \
  && python3 -m playwright install chromium
```

Then every invocation calls `python3 {SKILL_DIR}/scripts/extract_webpage.py …` and finds the deps via user-site.

### How the deps are used

`trafilatura` handles static HTML on its own. `curl` is in the cascade for Cloudflare-fronted sites where the requests library is 403'd; it ships on every macOS/Linux box, no install needed. `playwright` is only invoked when both static fetchers return sparse content -- that is, on genuinely JS-only sites. `readability-lxml`/`markdownify` are invoked when trafilatura succeeds at words but loses all the page's headings (the SPA-with-generic-divs case). Install everything up front so the fallbacks are ready when needed. Chromium downloads to `~/.cache/ms-playwright` and is shared across all venvs on the machine, so it's a one-time cost.

If the cascade reaches Playwright but it isn't installed, the script exits with the install command so the user can install it and re-run. The Readability fallback fails silently (the script just keeps trafilatura's output) if `readability-lxml` is missing.

> **Throughout the rest of this document, command examples use `python3` (Path B).** If you used Path A, substitute `{SKILL_DIR}/.venv/bin/python` for `python3` in every command.

## Process

### Step 1: Dry Run

Always start with a dry run to check what the script can see:

```bash
python3 {SKILL_DIR}/scripts/extract_webpage.py "<url>" --dry-run
```

This shows the detected title, author, date, site name, description, and word count. For crawl mode, add `--crawl` to the dry run to see the list of discovered pages.

The dry run reports which fetcher in the cascade succeeded (`Fetcher: requests` for plain HTML, `Fetcher: curl` for Cloudflare-fronted sites). If the word count is under 50, it notes that extraction will continue the cascade into Playwright. That's normal -- proceed to Step 2; the script handles the cascade automatically.

### Step 2: Extract

**Single page:**
```bash
python3 {SKILL_DIR}/scripts/extract_webpage.py "<url>" -o "<output-path>.md"
```

**Full site:**
```bash
python3 {SKILL_DIR}/scripts/extract_webpage.py "<url>" --crawl -o "<output-path>.md"
```

The `--crawl` flag discovers pages on the same domain (via sitemap, then static link extraction, then -- if neither yielded any links -- a rendered fetch of the start page) and extracts each one, combining them into a single document with a table of contents. It respects a 1-second delay between requests by default (`--delay` to adjust). Use `--max-pages` to cap the number of pages (default: 50).

On JS-only sites (React/Vue/Angular SPAs), discovery automatically falls back to rendering the start page and harvesting its DOM links, so crawl works on those sites too.

**Path scoping (default):** when the start URL has a non-root path like `/docs` or `/blog`, the crawl follows only links whose path starts with the same top-level segment. Crawling `https://example.com/docs` discovers `/docs/intro` and `/docs/api` but ignores `/about` or `/pricing`. This dramatically narrows app-style sites where the docs share a domain with a dApp UI. Caveats: peer sections (e.g. `/security` as a sibling of `/docs`) are excluded -- pass `--no-scope` to include them. Confirm with `--dry-run` first.

The script also filters out generic non-content URLs when crawling (tag pages, category pages, login pages, etc.). Override with `--exclude /pattern1/ /pattern2/` or disable with `--no-exclude`.

Other flags:
- `--no-links` strips hyperlinks from the output (cleaner for archival)
- `--include-images` adds image references
- `--delay N` seconds between crawl requests (default: 1.0)
- `--exclude /path/ /path/` custom URL patterns to exclude when crawling
- `--no-exclude` disable default URL filtering (include everything)
- `--no-scope` disable path-scoped crawling; follow any same-domain link
- `--render` always render with the headless browser (skip the static fetch); useful when a page returns just enough static content to clear the 50-word threshold but still misses the real article
- `--no-render` never use the headless browser; faster but will return empty content for JS-only pages
- `--fetcher {auto,requests,curl,playwright}` force a single fetcher instead of the cascade. Use `curl` for Cloudflare-fronted sites that 403 the requests library; use `playwright` to skip static fetchers entirely
- `--wait-until {domcontentloaded,load,networkidle}` Playwright wait condition (default: `domcontentloaded`). The default avoids 30-second timeouts on Mintlify/GitBook/Nextra sites that keep analytics websockets open forever

### Step 3: Post-Process

After extraction, read the output and check:

1. **Title**: Auto-detected titles sometimes grab the site name instead of the article title, or include " | Site Name" suffixes. Fix the `# Title` line. On big-typography landing pages where each word of the headline lives in its own styled `<span>` (e.g. "The / Claude / Code / Course" stacked vertically), trafilatura preserves the line breaks and the H1 lands fragmented across multiple lines. Merge them into a single H1 in post. Also check for a duplicate: trafilatura often keeps the article's own on-page heading as the first line of `content`, so the same title appears twice, once as the metadata `# H1` and again as a `##` right below it. Remove the second one when it just repeats the title.

2. **Metadata block**: Verify the source URL, author, date, and site name. Fill in anything missing. The metadata block should contain:
   - **Author** (if identifiable)
   - **Site** (domain or publication name)
   - **Date** (publication date if detectable)
   - **Source** (the original URL -- this is mandatory)
   - **Scraped** (today's date -- the script fills this in automatically)
   - **Description** (if the page has a meta description)

   The script's `Date` is a best guess, not a verified fact. On pages with no real publish date (reference docs, evergreen landing pages), it can fall back to today's date and look exactly like the `Scraped` line. If `Date` equals `Scraped` and the page itself has no visible publish date, drop the `Date` line rather than reporting a fabricated one.

3. **Content quality**: Trafilatura strips boilerplate well for most sites, but occasionally keeps cookie banners, newsletter signup text, or related-article links. Remove these. Conversely, it sometimes strips content that looks like boilerplate but isn't (sidebars with relevant data, footnotes). Check whether anything important is missing by visiting the URL.

4. **Structure**: The script preserves the page's heading hierarchy. If the original page had poor structure (all flat text, no headings), add section headings based on topic shifts. For multi-page crawls, each page becomes a `## Section` with its source URL noted.

5. **For multi-page crawls**: Review the table of contents. Remove pages that aren't useful (privacy policies, contact forms, 404s that slipped through). Reorder sections if the crawl order doesn't match logical reading order.

### Step 4: File It

Ask the user where to save it unless the project's CLAUDE.md or an existing folder convention makes it obvious. Match the filing pattern of neighboring documents if there is one.

**Filename:** Lowercase kebab-case — `<author-or-site>-<short-slug>.md`.

- **`<author-or-site>`** is the named author when available, otherwise the site brand. "Peter Attia" → `peter-attia`. When no named author, use the domain brand (e.g., `glyphosate-facts`).
- **`<short-slug>`** is a 3–6 word descriptive title. Keep the full page title in the `# H1` heading inside the file.
- **Normalize names:** strip to ASCII, lowercase, replace spaces with `-`, drop middle initials and apostrophes.

Examples: `peter-attia-metabolic-health-framework.md`, `glyphosate-facts-full-site.md`.

### Step 5: Cross-Reference

If the extracted page references studies, books, or videos already extracted in the project, add links in both directions. If it cites a study worth extracting, offer to run `extract-study` on it.

### Step 6: Commit

Add and commit with a descriptive message.

## Target Output Format

**Single page:**

```markdown
# Article Title

**Author:** Author Name
**Site:** Site Name
**Date:** 2026-01-15
**Source:** https://example.com/article
**Scraped:** 2026-04-21
**Description:** Brief description from meta tags

---

[clean article content in Markdown]
```

**Multi-page crawl:**

```markdown
# Site Name

**Source:** https://example.com/
**Author:** Author Name (if site-wide)
**Scraped:** 2026-04-21
**Description:** Site description

## Table of Contents

1. [Page Title](#page-title)
2. [Another Page](#another-page)
...

---

## Page Title

*URL: https://example.com/page-1*

[extracted content]

---

## Another Page

*URL: https://example.com/page-2*

[extracted content]

---
```

## Limitations

- **Authentication**: Cannot access pages behind login walls, paywalls, or CAPTCHAs. The headless browser uses a fresh profile with no saved cookies.
- **Cloudflare and similar WAFs**: The fetcher cascade handles most Cloudflare-fronted sites (Mintlify, GitBook, Docusaurus v3, Nextra) by falling through to the curl step, whose TLS fingerprint isn't on the requests-library blocklist. Active interstitials -- the "checking your browser" spinner, hCaptcha walls, JavaScript-only Turnstile challenges -- still block both curl and the headless browser. If a site serves a challenge page, both fetchers will return the stub HTML and extraction will be sparse.
- **Rate limiting**: Some sites block rapid requests. The `--delay` flag helps, but aggressive crawling may still get blocked. If extraction fails partway through a crawl, the script outputs what it collected.
- **Dynamic content**: Infinite-scroll pages and content that only loads on user interaction won't be captured -- the rendered fetch waits for `domcontentloaded` plus a brief content-selector poll but does not scroll or click. For full SPA crawls of an infinite-scroll feed, an explicit `--render --wait-until networkidle` may help, but only on sites whose network actually goes idle.
- **Speed**: Rendering a page is 5-15x slower than the static path (trafilatura or curl). The cascade only invokes Playwright when both static fetchers come back empty, so plain HTML and Cloudflare-fronted docs sites stay fast; only genuine SPAs incur the rendering cost.

## Troubleshooting

- **Empty extraction**: Try the URL in a browser to verify it's accessible. If the static fetch returned 0 words and the rendered fetch also returned little, the page may be a single-app shell with no readable prose, or it may be served a bot-challenge page.
- **"Playwright is not installed"**: Run the install command from the Setup section (`pip install playwright && playwright install chromium`), then re-run the extraction.
- **"Chromium isn't installed"**: Playwright was installed without its browser binary. Run `playwright install chromium`.
- **Garbled text**: Encoding issues. trafilatura handles most cases, but some older sites with mixed encodings may produce artifacts. Check the original page's charset.
- **Missing sections on crawl**: The sitemap may not list all pages, and link discovery only follows `<a>` tags on the start page. For sites with deep navigation, run the script on specific sub-pages individually.
- **Too many pages on crawl**: Use `--max-pages` to limit. Review the dry run page list first.
- **Render-mode timeout**: The default Playwright wait is `domcontentloaded`, which sidesteps the long-lived analytics/websocket connections that keep `networkidle` from firing on Mintlify, GitBook, and Nextra. If a site genuinely needs late-loading content, try `--wait-until networkidle` -- it's slower and may still time out, but it's there as a last resort.
- **Cloudflare 403**: If trafilatura returns nothing on a Cloudflare-fronted page, the cascade falls through to curl automatically. If curl also returns nothing, the site is probably serving an interstitial challenge page; try `--fetcher playwright` to render it through a real browser, but understand that Turnstile-style challenges still block headless Chromium.
