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

The script requires `trafilatura`. Install in the project venv:

```bash
source .venv/bin/activate && pip install trafilatura
```

## Process

### Step 1: Dry Run

Always start with a dry run to check what the script can see:

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_webpage.py "<url>" --dry-run
```

This shows the detected title, author, date, site name, description, and word count. For crawl mode, add `--crawl` to the dry run to see the list of discovered pages.

If the dry run shows no content or a very low word count, the page may be JavaScript-rendered (React/Next.js SPAs, heavy client-side rendering). In that case, tell the user the script can't reach the content and suggest they paste the page text manually or use a browser extension to copy as Markdown.

### Step 2: Extract

**Single page:**
```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_webpage.py "<url>" -o "<output-path>.md"
```

**Full site:**
```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_webpage.py "<url>" --crawl -o "<output-path>.md"
```

The `--crawl` flag discovers pages on the same domain (via sitemap or link following), extracts each one, and combines them into a single document with a table of contents. It respects a 1-second delay between requests by default (`--delay` to adjust). Use `--max-pages` to cap the number of pages (default: 50).

The script automatically filters out non-content URLs when crawling (tag pages, category pages, login pages, etc.). Override with `--exclude /pattern1/ /pattern2/` or disable with `--no-exclude`.

Other flags:
- `--no-links` strips hyperlinks from the output (cleaner for archival)
- `--include-images` adds image references
- `--delay N` seconds between crawl requests (default: 1.0)
- `--exclude /path/ /path/` custom URL patterns to exclude when crawling
- `--no-exclude` disable default URL filtering (include everything)

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

File the document based on its content:

- **Health/nutrition articles**: `archive/docs/<topic>/` (match existing neighbors)
- **Full site archives**: `archive/docs/<topic>/` with a descriptive name
- **Reference material**: `archive/docs/<topic>/reference/`
- **General web pages**: ask the user where they want it

Filename format: `<Descriptive Title> - <Author or Site>.md`

Examples:
- `Glyphosate Facts - Full Site.md`
- `Metabolic Health Framework - Peter Attia.md`
- `Statin Side Effects Overview - People's Pharmacy.md`

### Step 5: Cross-Reference

If the extracted page references studies, books, or videos already in the repo, add links in both directions. If it cites a study worth extracting, offer to run `extract-study` on it.

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

- **JavaScript-rendered pages**: trafilatura fetches raw HTML and cannot execute JavaScript. Sites built with React, Angular, or heavy client-side rendering may return no content. The dry run will show this (0 words). For these pages, suggest the user paste the content or use a browser-based copy tool.
- **Authentication**: Cannot access pages behind login walls, paywalls, or CAPTCHAs.
- **Rate limiting**: Some sites block rapid requests. The `--delay` flag helps, but aggressive crawling may still get blocked. If extraction fails partway through a crawl, the script outputs what it collected.
- **Dynamic content**: Infinite-scroll pages, lazy-loaded content, and interactive elements won't be captured.

## Troubleshooting

- **Empty extraction**: Try the URL in a browser to verify it's accessible. Check if the page requires JavaScript. Some CDN-protected sites (Cloudflare) may block non-browser requests.
- **Garbled text**: Encoding issues. trafilatura handles most cases, but some older sites with mixed encodings may produce artifacts. Check the original page's charset.
- **Missing sections on crawl**: The sitemap may not list all pages, and link discovery only follows `<a>` tags on the start page. For sites with deep navigation, run the script on specific sub-pages individually.
- **Too many pages on crawl**: Use `--max-pages` to limit. Review the dry run page list first.
