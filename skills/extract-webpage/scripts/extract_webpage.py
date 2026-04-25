#!/usr/bin/env python3
"""Extract web page content to clean Markdown using trafilatura.

Single-page mode (default):
    python extract_webpage.py "https://example.com/article" -o output.md

Multi-page crawl:
    python extract_webpage.py "https://example.com/" --crawl -o output.md

Dry run (preview metadata only):
    python extract_webpage.py "https://example.com/article" --dry-run
"""

import argparse
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import trafilatura
from trafilatura.settings import use_config


# Below this word count, the static fetch is treated as too sparse and we
# retry with a headless browser (covers React/Vue/Angular SPAs that render
# almost entirely client-side).
RENDER_FALLBACK_THRESHOLD = 50

PLAYWRIGHT_INSTALL_HINT = (
    "Install Playwright (one-time, ~300MB Chromium goes to ~/.cache/ms-playwright):\n"
    "    pip install playwright && playwright install chromium"
)

READABILITY_INSTALL_HINT = (
    "Install the Readability fallback so SPAs without semantic markup can be extracted:\n"
    "    pip install readability-lxml markdownify"
)


def slugify(text: str) -> str:
    """Match GitHub's heading-anchor scheme: lowercase, drop non-word chars
    except spaces and hyphens, collapse spaces to hyphens."""
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s


def make_config():
    config = use_config()
    config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
    return config


# URL path segments that almost never contain article content.
# Used as default --exclude patterns when crawling.
_DEFAULT_EXCLUDE = [
    "/tag/", "/tags/", "/category/", "/categories/",
    "/author/", "/authors/", "/page/", "/feed/",
    "/wp-json/", "/wp-admin/", "/wp-login",
    "/cart", "/checkout", "/my-account",
    "/privacy-policy", "/terms-of-service", "/cookie-policy",
    "/search", "/login", "/register", "/signup",
]


def _default_exclude_patterns():
    return list(_DEFAULT_EXCLUDE)


class PlaywrightMissing(Exception):
    """Playwright Python package is not installed."""


class ChromiumMissing(Exception):
    """Playwright is installed but Chromium browser binary is not."""


def fetch_rendered(url, timeout_ms=30000):
    """Fetch URL with headless Chromium and return fully-rendered HTML.

    Raises PlaywrightMissing if the Python package isn't installed,
    ChromiumMissing if the browser binary isn't installed.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PlaywrightMissing() from exc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                return page.content()
            finally:
                browser.close()
    except Exception as exc:
        msg = str(exc)
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            raise ChromiumMissing() from exc
        raise


def _extract_from_html(html, config, include_links, include_images, include_tables):
    metadata = trafilatura.extract_metadata(html)
    content = trafilatura.extract(
        html,
        output_format="markdown",
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        with_metadata=False,
        config=config,
    )
    return content, metadata


def _readability_extract(html, include_links=True):
    """Fallback extractor using Mozilla's Readability (via readability-lxml).

    Trafilatura is conservative: it discards anything that doesn't structurally
    look like an article (no <main>/<article>, low text density). Many SPAs
    render content into generic <div> containers that trafilatura rejects even
    though the prose is right there. Readability is greedy -- it scores every
    container for text density and picks the densest one. Returns Markdown.

    Returns None if either dependency is missing or extraction yields nothing.
    """
    try:
        from readability import Document
        from markdownify import markdownify as md
    except ImportError:
        return None

    try:
        doc = Document(html)
        content_html = doc.summary(html_partial=True)
    except Exception:
        return None

    if not content_html:
        return None

    strip_tags = ["div", "span"]
    if not include_links:
        strip_tags.append("a")
    markdown = md(content_html, heading_style="ATX", strip=strip_tags)
    return markdown.strip() or None


def fetch_and_extract(url, config=None, include_links=True, include_images=False,
                      include_tables=True, render="auto"):
    """Fetch a single URL and return (markdown_content, metadata, used_render).

    render:
        "auto"   - try static fetch first, fall back to headless browser if
                   the result is sparse (likely JS-rendered).
        "always" - skip the static fetch, always use the headless browser.
        "never"  - static fetch only; return whatever it produces.
    """
    config = config or make_config()
    extract_kwargs = dict(
        config=config, include_links=include_links,
        include_images=include_images, include_tables=include_tables,
    )

    static_content, static_metadata = None, None
    if render != "always":
        downloaded = trafilatura.fetch_url(url, config=config)
        if downloaded:
            static_content, static_metadata = _extract_from_html(downloaded, **extract_kwargs)
            words = len(static_content.split()) if static_content else 0
            if render == "never" or words >= RENDER_FALLBACK_THRESHOLD:
                return static_content, static_metadata, False

    rendered_html = fetch_rendered(url)
    content, metadata = _extract_from_html(rendered_html, **extract_kwargs)

    # Two failure modes for trafilatura on SPAs:
    #   1. Returns nothing -- page lacks any structure trafilatura recognizes.
    #   2. Returns plenty of words but strips all headings/lists -- the SPA's
    #      generic <div>s confuse trafilatura's structure detection so it dumps
    #      a wall of paragraphs. Result is technically extracted but unreadable.
    # Readability scores by text density, not semantic tags, so it survives both
    # cases. Compare the two and prefer Readability when it preserves structure
    # trafilatura lost.
    use_readability = False
    readability_md = None

    if not content or len(content.split()) < RENDER_FALLBACK_THRESHOLD:
        readability_md = _readability_extract(rendered_html, include_links=include_links)
        if readability_md and len(readability_md.split()) >= RENDER_FALLBACK_THRESHOLD:
            use_readability = True
    else:
        # Trafilatura returned content but possibly flattened. Compare structure.
        traf_headings = len(re.findall(r'^#{1,6} ', content, re.MULTILINE))
        if traf_headings == 0:
            readability_md = _readability_extract(rendered_html, include_links=include_links)
            if readability_md:
                read_headings = len(re.findall(r'^#{1,6} ', readability_md, re.MULTILINE))
                read_words = len(readability_md.split())
                traf_words = len(content.split())
                # Readability wins if it preserves multiple headings trafilatura
                # missed AND its word count is comparable (within 20%) -- guards
                # against Readability grabbing nav/sidebar in its dragnet.
                if read_headings >= 3 and read_words >= 0.8 * traf_words:
                    use_readability = True

    if use_readability:
        traf_words = len(content.split()) if content else 0
        print(f"  (using Readability fallback: trafilatura returned {traf_words} words "
              f"with no structure, Readability returned {len(readability_md.split())} words "
              f"with headings preserved)", file=sys.stderr)
        return readability_md, metadata, True

    return content, metadata, True


# File extensions Playwright can't render (it triggers a download instead),
# and trafilatura can't parse as HTML. Filtered out of discovered URLs.
_BINARY_EXTENSIONS = (
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z",
    ".dmg", ".exe", ".msi", ".pkg", ".deb", ".rpm",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".mp3", ".mp4", ".mov", ".avi", ".webm", ".wav", ".ogg",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".json", ".xml",
)


def _extract_same_domain_links(html, start_url, domain):
    """Parse HTML and return deduplicated same-domain hrefs (no query/fragment).

    Skips URLs whose path ends in a known binary extension -- Playwright
    can't render those (it triggers a file download instead).
    """
    from lxml import html as lxml_html
    tree = lxml_html.fromstring(html)
    tree.make_links_absolute(start_url)

    urls = []
    for element, _attr, link, _pos in tree.iterlinks():
        if element.tag != "a" or urlparse(link).netloc != domain:
            continue
        clean = link.split("#")[0].split("?")[0].rstrip("/")
        if not clean:
            continue
        path_lower = urlparse(clean).path.lower()
        if path_lower.endswith(_BINARY_EXTENSIONS):
            continue
        if clean not in urls:
            urls.append(clean)
    return urls


def _path_prefix_for_scope(start_url):
    """Return the path prefix that other URLs must match to be in scope.

    "https://example.com/docs"        -> "/docs"
    "https://example.com/docs/"       -> "/docs"
    "https://example.com/docs/intro"  -> "/docs"
    "https://example.com/"            -> "" (no scoping)
    "https://example.com"             -> "" (no scoping)

    Only the top-level path segment is used. A start URL deep inside a
    section still scopes to the section root, so /docs/intro will still
    crawl /docs/api.
    """
    path = urlparse(start_url).path.strip("/")
    if not path:
        return ""
    first_segment = path.split("/", 1)[0]
    return f"/{first_segment}"


def discover_pages(start_url, config=None, max_pages=50, exclude_patterns=None,
                   render="auto", scope=True):
    """Discover pages on the same domain starting from a URL.

    Tries a sitemap first, then static link extraction, then a rendered fetch
    (Playwright) if the static page yields no same-domain links -- which is
    the signature of a client-rendered SPA. Returns a deduplicated list of
    URLs including the start URL.

    render: "auto" (sitemap -> static -> rendered fallback),
            "always" (skip static, go straight to rendered),
            "never" (no rendered fallback even if static yields nothing).
    exclude_patterns: list of substrings to exclude from discovered URLs.
    scope: when True (default), restrict discovery to URLs whose path starts
           with the same top-level segment as start_url (e.g. /docs/* when
           starting at /docs). Has no effect when start_url is the site root.
    """
    config = config or make_config()
    domain = urlparse(start_url).netloc
    exclude_patterns = exclude_patterns or []
    scope_prefix = _path_prefix_for_scope(start_url) if scope else ""

    # Try sitemap first -- works regardless of how the site renders
    from trafilatura import sitemaps
    sitemap_urls = sitemaps.sitemap_search(start_url)

    if sitemap_urls:
        urls = [u for u in sitemap_urls if urlparse(u).netloc == domain]
    else:
        urls = []
        if render != "always":
            downloaded = trafilatura.fetch_url(start_url, config=config)
            if downloaded:
                urls = _extract_same_domain_links(downloaded, start_url, domain)

        # Static returned nothing useful: probably a JS-only shell. Render it.
        need_render = (render == "always") or (render == "auto" and not urls)
        if need_render:
            print("Rendering start page to discover links (static HTML had none)...",
                  file=sys.stderr)
            rendered_html = fetch_rendered(start_url)
            urls = _extract_same_domain_links(rendered_html, start_url, domain)

        if not urls:
            return [start_url]

    # Apply exclude patterns
    if exclude_patterns:
        before = len(urls)
        urls = [u for u in urls
                if not any(pat in u for pat in exclude_patterns)]
        excluded = before - len(urls)
        if excluded:
            print(f"Excluded {excluded} URLs matching patterns: {exclude_patterns}",
                  file=sys.stderr)

    # Apply path scoping: when starting at /docs, only crawl /docs/*. The start
    # URL itself is exempt (always kept). A common surprise is when a sibling
    # section (e.g. /security as a peer of /docs) holds related docs -- the
    # user can disable scoping with --no-scope to capture those.
    if scope_prefix:
        start_clean = start_url.rstrip("/")
        before = len(urls)
        urls = [u for u in urls
                if u == start_clean
                or urlparse(u).path.startswith(scope_prefix)]
        scoped_out = before - len(urls)
        if scoped_out:
            print(f"Path-scoped to {scope_prefix}/* (excluded {scoped_out} URLs "
                  f"outside scope; use --no-scope to disable)",
                  file=sys.stderr)

    # Ensure start URL is first
    start_clean = start_url.rstrip("/")
    if start_clean in urls:
        urls.remove(start_clean)
    urls.insert(0, start_clean)

    if len(urls) > max_pages:
        print(f"Found {len(urls)} pages, limiting to {max_pages}", file=sys.stderr)
        urls = urls[:max_pages]

    return urls


def dry_run(url, crawl=False, render="auto", scope=True):
    """Preview metadata and page list without extracting full content."""
    config = make_config()

    print("=== Dry Run ===")
    print(f"URL: {url}")
    print()

    downloaded = trafilatura.fetch_url(url, config=config)
    if not downloaded:
        print("ERROR: Could not fetch URL", file=sys.stderr)
        return

    metadata = trafilatura.extract_metadata(downloaded)
    content = trafilatura.extract(downloaded, output_format="markdown", config=config)
    word_count = len(content.split()) if content else 0

    print(f"Title:       {metadata.title if metadata and metadata.title else '(not detected)'}")
    print(f"Author:      {metadata.author if metadata and metadata.author else '(not detected)'}")
    print(f"Date:        {metadata.date if metadata and metadata.date else '(not detected)'}")
    print(f"Site name:   {metadata.sitename if metadata and metadata.sitename else '(not detected)'}")
    desc = (metadata.description or "(not detected)")[:200] if metadata else "(not detected)"
    print(f"Description: {desc}")
    print(f"Words:       {word_count}")
    print(f"Content:     {'Yes' if content else 'No extractable content'}")

    if word_count < RENDER_FALLBACK_THRESHOLD:
        print()
        print("Page looks sparse or JS-rendered. Extraction will retry with a")
        print("headless browser. Pass --no-render to disable that fallback.")

    if crawl:
        print()
        print("=== Discovered Pages ===")
        pages = discover_pages(url, config=config,
                               exclude_patterns=_default_exclude_patterns(),
                               render=render, scope=scope)
        for i, page_url in enumerate(pages, 1):
            print(f"  {i:3d}. {page_url}")
        print(f"\nTotal: {len(pages)} pages")


def build_single_page_markdown(url, content, metadata):
    """Build Markdown for a single-page extraction."""
    lines = []

    title = metadata.title if metadata and metadata.title else urlparse(url).netloc
    lines.append(f"# {title}")
    lines.append("")

    if metadata:
        if metadata.author:
            lines.append(f"**Author:** {metadata.author}")
        if metadata.sitename:
            lines.append(f"**Site:** {metadata.sitename}")
        if metadata.date:
            lines.append(f"**Date:** {metadata.date}")
    lines.append(f"**Source:** {url}")
    if metadata and metadata.description:
        lines.append(f"**Description:** {metadata.description}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(content)
    lines.append("")

    return "\n".join(lines)


def build_multi_page_markdown(start_url, pages, site_metadata):
    """Build Markdown for a multi-page crawl.

    pages: list of (url, content, metadata) tuples
    site_metadata: metadata from the start page (used for the document title)
    """
    lines = []

    site_name = ""
    if site_metadata and site_metadata.sitename:
        site_name = site_metadata.sitename
    elif site_metadata and site_metadata.title:
        site_name = site_metadata.title
    else:
        site_name = urlparse(start_url).netloc

    lines.append(f"# {site_name}")
    lines.append("")
    lines.append(f"**Source:** {start_url}")
    if site_metadata and site_metadata.author:
        lines.append(f"**Author:** {site_metadata.author}")
    if site_metadata and site_metadata.description:
        lines.append(f"**Description:** {site_metadata.description}")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for i, (url, content, meta) in enumerate(pages, 1):
        page_title = meta.title if meta and meta.title else url
        anchor = slugify(page_title)
        lines.append(f"{i}. [{page_title}](#{anchor})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Each page as a section
    for url, content, meta in pages:
        page_title = meta.title if meta and meta.title else url
        lines.append(f"## {page_title}")
        lines.append("")
        lines.append(f"*URL: {url}*")
        lines.append("")
        if content:
            lines.append(content)
        else:
            lines.append("*(No extractable content)*")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract web page content to Markdown"
    )
    parser.add_argument("url", help="URL to extract")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview metadata without extracting")
    parser.add_argument("--crawl", action="store_true",
                        help="Crawl the site and extract multiple pages")
    parser.add_argument("--max-pages", type=int, default=50,
                        help="Max pages to crawl (default: 50)")
    parser.add_argument("--no-links", action="store_true",
                        help="Strip hyperlinks from output")
    parser.add_argument("--include-images", action="store_true",
                        help="Include image references in output")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between requests when crawling (default: 1.0)")
    parser.add_argument("--exclude", nargs="*",
                        help="URL substrings to exclude when crawling "
                             "(e.g., /tag/ /category/). Defaults filter common "
                             "non-content paths; pass explicit patterns to override.")
    parser.add_argument("--no-exclude", action="store_true",
                        help="Disable default URL exclusion patterns when crawling")
    parser.add_argument("--no-scope", action="store_true",
                        help="Disable path-scoped crawling. By default, when "
                             "crawling from a non-root URL like /docs, only "
                             "URLs under /docs/* are followed. --no-scope "
                             "follows any same-domain link.")
    render_group = parser.add_mutually_exclusive_group()
    render_group.add_argument("--render", action="store_const", dest="render",
                              const="always",
                              help="Always render with a headless browser "
                                   "(skip the fast static fetch)")
    render_group.add_argument("--no-render", action="store_const", dest="render",
                              const="never",
                              help="Never render; return whatever the static "
                                   "fetch produces (faster, may miss JS pages)")
    parser.set_defaults(render="auto")

    args = parser.parse_args()
    config = make_config()
    include_links = not args.no_links

    if args.dry_run:
        dry_run(args.url, crawl=args.crawl, render=args.render,
                scope=not args.no_scope)
        return

    def _extract_one(url, fatal_on_error=True):
        try:
            return fetch_and_extract(
                url, config=config, include_links=include_links,
                include_images=args.include_images, render=args.render,
            )
        except PlaywrightMissing:
            print(f"\nERROR: '{url}' looks JavaScript-rendered and Playwright "
                  "is not installed.", file=sys.stderr)
            print(PLAYWRIGHT_INSTALL_HINT, file=sys.stderr)
            sys.exit(1)
        except ChromiumMissing:
            print(f"\nERROR: '{url}' needs a headless browser but Chromium "
                  "isn't installed.", file=sys.stderr)
            print("    playwright install chromium", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            # Per-page failures (timeouts, downloads triggered by binary URLs,
            # transient network errors) shouldn't kill an in-progress crawl.
            if fatal_on_error:
                raise
            print(f"      (error: {exc})", file=sys.stderr)
            return None, None, False

    if args.crawl:
        # Multi-page mode
        if args.no_exclude:
            exclude = []
        elif args.exclude:
            exclude = args.exclude
        else:
            exclude = _default_exclude_patterns()
        try:
            urls = discover_pages(args.url, config=config,
                                  max_pages=args.max_pages,
                                  exclude_patterns=exclude, render=args.render,
                                  scope=not args.no_scope)
        except PlaywrightMissing:
            print(f"\nERROR: '{args.url}' has no static links to crawl and "
                  "Playwright is not installed.", file=sys.stderr)
            print(PLAYWRIGHT_INSTALL_HINT, file=sys.stderr)
            sys.exit(1)
        except ChromiumMissing:
            print(f"\nERROR: '{args.url}' needs a headless browser to discover "
                  "links but Chromium isn't installed.", file=sys.stderr)
            print("    playwright install chromium", file=sys.stderr)
            sys.exit(1)
        print(f"Extracting {len(urls)} pages...", file=sys.stderr)

        pages = []
        site_metadata = None

        for i, url in enumerate(urls):
            content, metadata, rendered = _extract_one(url, fatal_on_error=False)
            if i == 0:
                site_metadata = metadata
            if content:
                pages.append((url, content, metadata))
                words = len(content.split())
                tag = " [rendered]" if rendered else ""
                print(f"  [{i+1}/{len(urls)}] {url} ({words} words){tag}",
                      file=sys.stderr)
            else:
                print(f"  [{i+1}/{len(urls)}] {url} (skipped, no content)", file=sys.stderr)

            if i < len(urls) - 1:
                time.sleep(args.delay)

        if not pages:
            print("ERROR: No content extracted from any page", file=sys.stderr)
            sys.exit(1)

        total_words = sum(len(c.split()) for _, c, _ in pages)
        output = build_multi_page_markdown(args.url, pages, site_metadata)
        print(f"\nExtracted {len(pages)} pages ({total_words} words total)",
              file=sys.stderr)

    else:
        # Single-page mode
        content, metadata, rendered = _extract_one(args.url)
        if not content:
            print(f"ERROR: Could not extract content from {args.url}",
                  file=sys.stderr)
            sys.exit(1)

        output = build_single_page_markdown(args.url, content, metadata)
        tag = " (rendered with headless browser)" if rendered else ""
        print(f"Extracted {len(content.split())} words{tag}", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
