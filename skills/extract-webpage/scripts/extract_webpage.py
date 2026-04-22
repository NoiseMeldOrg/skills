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


def fetch_and_extract(url, config=None, include_links=True, include_images=False,
                      include_tables=True):
    """Fetch a single URL and return (markdown_content, metadata)."""
    config = config or make_config()

    downloaded = trafilatura.fetch_url(url, config=config)
    if not downloaded:
        return None, None

    metadata = trafilatura.extract_metadata(downloaded)

    content = trafilatura.extract(
        downloaded,
        output_format="markdown",
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        with_metadata=False,
        config=config,
    )

    return content, metadata


def discover_pages(start_url, config=None, max_pages=50, exclude_patterns=None):
    """Discover pages on the same domain starting from a URL.

    Uses trafilatura's sitemap and link extraction. Returns a deduplicated
    list of URLs including the start URL.

    exclude_patterns: list of substrings to exclude from discovered URLs
                      (e.g., ["/tag/", "/category/", "/author/"])
    """
    config = config or make_config()
    domain = urlparse(start_url).netloc
    exclude_patterns = exclude_patterns or []

    # Try sitemap first
    from trafilatura import sitemaps
    sitemap_urls = sitemaps.sitemap_search(start_url)

    if sitemap_urls:
        urls = [u for u in sitemap_urls if urlparse(u).netloc == domain]
    else:
        # Fall back to link extraction from the start page
        downloaded = trafilatura.fetch_url(start_url, config=config)
        if not downloaded:
            return [start_url]

        from lxml import html as lxml_html
        tree = lxml_html.fromstring(downloaded)
        tree.make_links_absolute(start_url)

        urls = []
        for element, _attr, link, _pos in tree.iterlinks():
            if element.tag == "a" and urlparse(link).netloc == domain:
                clean = link.split("#")[0].split("?")[0].rstrip("/")
                if clean not in urls:
                    urls.append(clean)

    # Apply exclude patterns
    if exclude_patterns:
        before = len(urls)
        urls = [u for u in urls
                if not any(pat in u for pat in exclude_patterns)]
        excluded = before - len(urls)
        if excluded:
            print(f"Excluded {excluded} URLs matching patterns: {exclude_patterns}",
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


def dry_run(url, crawl=False):
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

    if crawl:
        print()
        print("=== Discovered Pages ===")
        pages = discover_pages(url, config=config,
                               exclude_patterns=_default_exclude_patterns())
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

    args = parser.parse_args()
    config = make_config()
    include_links = not args.no_links

    if args.dry_run:
        dry_run(args.url, crawl=args.crawl)
        return

    if args.crawl:
        # Multi-page mode
        if args.no_exclude:
            exclude = []
        elif args.exclude:
            exclude = args.exclude
        else:
            exclude = _default_exclude_patterns()
        urls = discover_pages(args.url, config=config, max_pages=args.max_pages,
                              exclude_patterns=exclude)
        print(f"Extracting {len(urls)} pages...", file=sys.stderr)

        pages = []
        site_metadata = None

        for i, url in enumerate(urls):
            content, metadata = fetch_and_extract(
                url, config=config, include_links=include_links,
                include_images=args.include_images,
            )
            if i == 0:
                site_metadata = metadata
            if content:
                pages.append((url, content, metadata))
                words = len(content.split())
                print(f"  [{i+1}/{len(urls)}] {url} ({words} words)", file=sys.stderr)
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
        content, metadata = fetch_and_extract(
            args.url, config=config, include_links=include_links,
            include_images=args.include_images,
        )
        if not content:
            print(f"ERROR: Could not extract content from {args.url}",
                  file=sys.stderr)
            sys.exit(1)

        output = build_single_page_markdown(args.url, content, metadata)
        print(f"Extracted {len(content.split())} words", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
