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

The script tries a fast static fetch first. If the result looks sparse (under 50 words -- the signature of a JavaScript-rendered SPA), it automatically retries with a headless Chromium browser via Playwright and runs trafilatura on the fully-rendered HTML. So React, Vue, and Angular pages work the same way as plain HTML pages.

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

The script requires `trafilatura`, plus `playwright` for the JS-rendering fallback. Install both in the project venv:

```bash
source .venv/bin/activate && pip install trafilatura playwright && playwright install chromium
```

`trafilatura` handles static HTML on its own. `playwright` is only invoked when a page returns sparse content -- but install both up front so the JS fallback is ready when needed. Chromium downloads to `~/.cache/ms-playwright` and is shared across all venvs on the machine, so it's a one-time cost.

If a JS page is encountered without Playwright installed, the script exits with the install command so the user can install it and re-run.

## Process

### Step 1: Dry Run

Always start with a dry run to check what the script can see:

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_webpage.py "<url>" --dry-run
```

This shows the detected title, author, date, site name, description, and word count. For crawl mode, add `--crawl` to the dry run to see the list of discovered pages.

If the word count is under 50, the dry run notes that the page looks JS-rendered and that extraction will retry with a headless browser. That's normal -- proceed to Step 2; the script handles the fallback automatically.

### Step 2: Extract

**Single page:**
```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_webpage.py "<url>" -o "<output-path>.md"
```

**Full site:**
```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_webpage.py "<url>" --crawl -o "<output-path>.md"
```

The `--crawl` flag discovers pages on the same domain (via sitemap, then static link extraction, then -- if neither yielded any links -- a rendered fetch of the start page) and extracts each one, combining them into a single document with a table of contents. It respects a 1-second delay between requests by default (`--delay` to adjust). Use `--max-pages` to cap the number of pages (default: 50).

On JS-only sites (React/Vue/Angular SPAs), discovery automatically falls back to rendering the start page and harvesting its DOM links, so crawl works on those sites too.

The script automatically filters out non-content URLs when crawling (tag pages, category pages, login pages, etc.). Override with `--exclude /pattern1/ /pattern2/` or disable with `--no-exclude`.

Other flags:
- `--no-links` strips hyperlinks from the output (cleaner for archival)
- `--include-images` adds image references
- `--delay N` seconds between crawl requests (default: 1.0)
- `--exclude /path/ /path/` custom URL patterns to exclude when crawling
- `--no-exclude` disable default URL filtering (include everything)
- `--render` always render with the headless browser (skip the static fetch); useful when a page returns just enough static content to clear the 50-word threshold but still misses the real article
- `--no-render` never use the headless browser; faster but will return empty content for JS-only pages

### Step 3: Post-Process

After extraction, read the output and check:

1. **Title**: Auto-detected titles sometimes grab the site name instead of the article title, or include " | Site Name" suffixes. Fix the `# Title` line.

2. **Metadata block**: Verify the source URL, author, date, and site name. Fill in anything missing. The metadata block should contain:
   - **Author** (if identifiable)
   - **Site** (domain or publication name)
   - **Date** (publication date if detectable)
   - **Source** (the original URL -- this is mandatory)
   - **Scraped** (today's date)
   - **Description** (if the page has a meta description)

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
- **Aggressive anti-bot protection**: Cloudflare's "checking your browser" interstitial, hCaptcha walls, and similar bot-detection layers can still block the headless browser. trafilatura's static fetch will fail outright; the rendered fetch may also be served the challenge page.
- **Rate limiting**: Some sites block rapid requests. The `--delay` flag helps, but aggressive crawling may still get blocked. If extraction fails partway through a crawl, the script outputs what it collected.
- **Dynamic content**: Infinite-scroll pages and content that only loads on user interaction won't be captured -- the rendered fetch waits for `networkidle` but does not scroll or click.
- **Speed**: Rendering a page is 5-15x slower than the static fetch. Crawling many JS-rendered pages will be noticeably slow; consider `--max-pages` to keep it bounded.

## Troubleshooting

- **Empty extraction**: Try the URL in a browser to verify it's accessible. If the static fetch returned 0 words and the rendered fetch also returned little, the page may be a single-app shell with no readable prose, or it may be served a bot-challenge page.
- **"Playwright is not installed"**: Run the install command from the Setup section (`pip install playwright && playwright install chromium`), then re-run the extraction.
- **"Chromium isn't installed"**: Playwright was installed without its browser binary. Run `playwright install chromium`.
- **Garbled text**: Encoding issues. trafilatura handles most cases, but some older sites with mixed encodings may produce artifacts. Check the original page's charset.
- **Missing sections on crawl**: The sitemap may not list all pages, and link discovery only follows `<a>` tags on the start page. For sites with deep navigation, run the script on specific sub-pages individually.
- **Too many pages on crawl**: Use `--max-pages` to limit. Review the dry run page list first.
- **Render-mode timeout**: Some sites never reach `networkidle` (live tickers, analytics pings). If the rendered fetch times out, the article is probably available before networkidle fires anyway -- consider piping the relevant section in manually if this becomes a recurring problem.
