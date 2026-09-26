#!/usr/bin/env python3
"""
Extract a research study / journal article PDF into structured Markdown.

Detects IMRaD section headings, pulls metadata from the first page
(title, authors, journal, year, DOI), and produces a clean Markdown file
with a metadata header + section structure + preserved references.

Usage:
    python extract_study_pdf.py <pdf_path> [-o output.md] [--dry-run] [--layout]
"""

import argparse
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=".*FontBBox.*")
warnings.filterwarnings("ignore", category=UserWarning)

import pdfplumber

# Canonical section names and the aliases that map to them.
SECTION_ALIASES = [
    ("Abstract",          [r"abstract", r"summary"]),
    ("Introduction",      [r"introduction", r"background"]),
    ("Methods",           [r"methods", r"materials and methods", r"methodology",
                           r"patients and methods", r"study design", r"methods and materials",
                           r"subjects and methods", r"experimental procedures"]),
    ("Results",           [r"results", r"findings"]),
    ("Discussion",        [r"discussion"]),
    ("Conclusion",        [r"conclusion", r"conclusions", r"concluding remarks"]),
    ("Acknowledgments",   [r"acknowledgments", r"acknowledgements"]),
    ("Funding",           [r"funding", r"funding information", r"funding sources"]),
    ("Conflicts of Interest", [r"conflict of interest", r"conflicts of interest",
                                r"competing interests", r"declaration of interests"]),
    ("Data Availability", [r"data availability statement", r"data availability"]),
    ("What is Known",     [r"what is known"]),
    ("What This Study Adds", [r"what does this study add", r"what this study adds"]),
    ("References",        [r"references", r"bibliography", r"literature cited",
                           r"works cited"]),
]

# Build a single regex for heading detection.
# Matches lines that are JUST a heading (optional numbering, optional trailing colon/period).
HEADING_PATTERNS = []
for canonical, aliases in SECTION_ALIASES:
    for a in aliases:
        HEADING_PATTERNS.append((canonical, re.compile(
            rf"^\s*(?:\d+\.?\s*)?{a}\s*[:.]?\s*$", re.IGNORECASE)))

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
PMID_RE = re.compile(r"\bPMID[:\s]*(\d{6,9})\b", re.IGNORECASE)
PMCID_RE = re.compile(r"\bPMC\d{6,9}\b", re.IGNORECASE)

# Page-header / footer noise found on NIHMS author manuscripts and similar
# repeating chrome that the PDF text layer interleaves into the body.
NOISE_LINE_PATTERNS = [
    re.compile(r"^HHS Public Access$", re.IGNORECASE),
    re.compile(r"^Author manuscript$", re.IGNORECASE),
    re.compile(r"^Author$"),                                     # NIHMS sidebar fragment
    re.compile(r"^Manuscript$"),                                  # NIHMS sidebar fragment
    re.compile(r"^[A-Z][\w\s\-']+\set al\.\s+Page\s+\d+$"),       # "Colgan et al. Page 4"
    re.compile(r".*Author manuscript;\s*available in PMC.*", re.IGNORECASE),
    re.compile(r"^Published in final edited form as:?\s*$", re.IGNORECASE),
    re.compile(r"^Page\s+\d+\s+of\s+\d+$", re.IGNORECASE),
]

# Tokens that look like correlation-table cells that pdfplumber returned in
# right-to-left order (e.g. "**82.0" instead of "0.28**", "*02.0−" instead of
# "−0.20*"). Used as a heuristic to suggest --layout retry.
REVERSED_CELL_RE = re.compile(r"^\*{1,2}\d+\.\d+−?$|^−?\*{1,2}\d{1,2}\.\d{1,2}$")


def extract_pages(pdf_path: str, use_layout: bool = False) -> list[str]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if use_layout:
                text = (page.extract_text(layout=True) or "").replace('\x00', '')
            else:
                text = (page.extract_text() or "").replace('\x00', '')
            pages.append(text)
    return pages


def clean_text(text: str) -> str:
    """Drop standalone page numbers, NIHMS chrome, and repeating page-header
    pollution; collapse blank lines."""
    lines = text.split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if re.match(r"^\d{1,4}$", s):
            continue
        if any(p.match(s) for p in NOISE_LINE_PATTERNS):
            continue
        out.append(line.rstrip())
    joined = "\n".join(out)
    joined = re.sub(r"\n{3,}", "\n\n", joined)
    return joined


def detect_reversed_cells(text: str) -> int:
    """Count tokens that look like correlation-table cells reversed
    character-by-character (a known pdfplumber failure mode for some journals).
    Returns the count so the caller can decide whether to warn."""
    tokens = text.split()
    return sum(1 for t in tokens if REVERSED_CELL_RE.match(t))


def extract_metadata(pages: list[str]) -> dict:
    """Pull best-guess metadata from the first 2 pages."""
    head = "\n".join(pages[:2])
    meta = {
        "title": None,
        "authors": None,
        "journal": None,
        "year": None,
        "doi": None,
        "pmid": None,
        "pmcid": None,
    }

    # DOI. Two-column layouts sometimes cut a DOI short where it wraps at a
    # column boundary (e.g. "10.1371/journal." with the rest of the line
    # bleeding in from the neighboring column) while the same DOI appears
    # complete elsewhere on the page (running footer, citation block). Take
    # the longest match rather than just the first.
    doi_matches = [dm.group(0).rstrip(".,;)") for dm in DOI_RE.finditer(head)]
    if doi_matches:
        meta["doi"] = max(doi_matches, key=len)

    # PMID / PMCID
    m = PMID_RE.search(head)
    if m:
        meta["pmid"] = m.group(1)
    m = PMCID_RE.search(head)
    if m:
        meta["pmcid"] = m.group(0)

    # Year (first 4-digit year on page 1)
    m = YEAR_RE.search(pages[0] if pages else "")
    if m:
        meta["year"] = m.group(0)

    # Title: longest non-trivial line in the first ~25 lines of page 1
    # that isn't a journal header, DOI, NIHMS cover matter, or copyright.
    # Some journals set the article-type label ("Research Article", "Case
    # Report", ...) directly in front of the title with no line break, and
    # pdfplumber sometimes drops the space between the two words entirely
    # (e.g. "RESEARCHARTICLESeroprevalence of..."). Strip that label prefix
    # instead of discarding the whole line, or the real title goes with it.
    label_prefix_re = re.compile(
        r'^(research\s*article|review\s*article|original\s*article|'
        r'case\s*report|short\s*communication|brief\s*report|'
        r'original\s*research)\s*[:.\-]?\s*',
        re.IGNORECASE,
    )
    if pages:
        first_lines = [l.strip() for l in pages[0].split("\n")[:25] if l.strip()]
        candidates = []
        for line in first_lines:
            line = label_prefix_re.sub('', line).strip()
            if not line:
                continue
            lower = line.lower()
            if len(line) < 15 or len(line) > 250:
                continue
            if any(skip in lower for skip in [
                "doi", "copyright", "©", "http", "www.", "issn",
                "received", "accepted", "published in final", "volume", "license",
                "open access", "original article", "review article",
                "hhs public access", "author manuscript",
                "available in pmc",
            ]):
                continue
            if DOI_RE.search(line):
                continue
            candidates.append(line)
        if candidates:
            # Title is usually the first long-ish line, possibly spanning up to
            # 4–5 lines in long-titled papers. Glue continuations until we hit
            # what looks like the author line (starts uppercase, contains commas
            # and a degree token like "PhD" / "MD" / "MS").
            meta["title"] = candidates[0]
            for nxt in candidates[1:6]:
                if not nxt:
                    break
                # Stop at author lines: a degree token after a comma (accepting
                # both "PhD" and the dotted "Ph.D." form journals commonly use),
                # or 2+ letter-immediately-followed-by-digit tokens, which is
                # how superscript affiliation markers show up once pdfplumber
                # flattens them into the text layer (e.g. "GetahunID 1",
                # "Mamo2") — real title text essentially never does this.
                if re.search(
                    r",\s*(Ph\.?\s?D\.?|M\.?\s?D\.?|M\.?\s?S\.?|MSc|M\.?\s?P\.?\s?H\.?|"
                    r"R\.?\s?N\.?|D\.?\s?O\.?|D\.?\s?D\.?\s?S\.?|D\.?\s?V\.?\s?M\.?|"
                    r"Pharm\.?\s?D\.?|MBBS)\b",
                    nxt,
                ):
                    break
                if len(re.findall(r'[a-zA-Z]\d', nxt)) >= 2:
                    break
                # Continuation if it starts lowercase, ends with hyphen, or is
                # short enough to plausibly be a title fragment.
                looks_like_continuation = (
                    nxt[0].islower()
                    or meta["title"].rstrip().endswith("-")
                    or len(nxt) < 80
                )
                if not looks_like_continuation:
                    break
                # Join hyphenated line-breaks without a space; otherwise add a space.
                if meta["title"].rstrip().endswith("-"):
                    meta["title"] = meta["title"].rstrip() + nxt
                else:
                    meta["title"] = meta["title"] + " " + nxt

    return meta


def find_sections(full_text: str) -> list[tuple[str, int]]:
    """Return [(canonical_name, line_index), ...] sorted by position."""
    lines = full_text.split("\n")
    hits = []
    seen = set()
    for i, line in enumerate(lines):
        for canonical, pat in HEADING_PATTERNS:
            if pat.match(line):
                # Only take the FIRST occurrence of each canonical section
                if canonical in seen:
                    continue
                # Abstract must appear early; Methods/Results/Discussion after Abstract
                hits.append((canonical, i))
                seen.add(canonical)
                break
    hits.sort(key=lambda x: x[1])
    return hits


def build_markdown(pdf_path: str, pages: list[str]) -> tuple[str, dict, list]:
    meta = extract_metadata(pages)
    full = clean_text("\n".join(pages))
    sections = find_sections(full)

    # Build header
    lines_out = []
    title = meta["title"] or Path(pdf_path).stem
    lines_out.append(f"# {title}")
    lines_out.append("")
    if meta["authors"]:
        lines_out.append(f"**Authors:** {meta['authors']}")
    if meta["journal"]:
        lines_out.append(f"**Journal:** {meta['journal']}")
    if meta["year"]:
        lines_out.append(f"**Year:** {meta['year']}")
    if meta["doi"]:
        lines_out.append(f"**DOI:** {meta['doi']}")
    if meta["pmid"]:
        lines_out.append(f"**PMID:** {meta['pmid']}")
    if meta["pmcid"]:
        lines_out.append(f"**PMCID:** {meta['pmcid']}")
    lines_out.append("**Study design:** _fill in manually_")
    lines_out.append("")
    lines_out.append("## Key Findings")
    lines_out.append("")
    lines_out.append("- _fill in after reading_")
    lines_out.append("")
    lines_out.append("---")
    lines_out.append("")

    # Body: if we found sections, slice; otherwise dump flat
    body_lines = full.split("\n")
    if sections:
        # Prepend anything before first section as "Front matter"
        first_idx = sections[0][1]
        if first_idx > 0:
            front = "\n".join(body_lines[:first_idx]).strip()
            if front:
                lines_out.append("<!-- Front matter (title page, abstract header, etc.) -->")
                lines_out.append("")
                lines_out.append(front)
                lines_out.append("")
        for i, (name, start) in enumerate(sections):
            end = sections[i + 1][1] if i + 1 < len(sections) else len(body_lines)
            chunk = "\n".join(body_lines[start + 1:end]).strip()
            lines_out.append(f"## {name}")
            lines_out.append("")
            lines_out.append(chunk)
            lines_out.append("")
            if name != "References" and i + 1 < len(sections):
                pass  # no extra divider between sections
        lines_out.append("")
    else:
        lines_out.append("<!-- No IMRaD sections detected — flat extraction -->")
        lines_out.append("")
        lines_out.append(full)

    return "\n".join(lines_out), meta, sections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Path to study PDF")
    ap.add_argument("-o", "--output", help="Output .md path (default: alongside PDF)")
    ap.add_argument("--dry-run", action="store_true", help="Print detected metadata + sections without writing")
    ap.add_argument("--layout", action="store_true", help="Use pdfplumber layout=True mode for column-heavy PDFs")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    pages = extract_pages(str(pdf_path), use_layout=args.layout)
    md, meta, sections = build_markdown(str(pdf_path), pages)

    reversed_hits = detect_reversed_cells(md)
    if reversed_hits >= 10 and not args.layout:
        print(
            f"WARNING: detected {reversed_hits} tokens that look like correlation-table\n"
            f"cells extracted in right-to-left order (e.g. '**82.0' instead of '0.28**').\n"
            f"This usually means a table was rendered with reversed text direction.\n"
            f"Try rerunning with --layout, or reconstruct the affected table from the\n"
            f"published HTML (e.g. PMC) before filing the .md.",
            file=sys.stderr,
        )

    if args.dry_run:
        print("=" * 60)
        print(f"File: {pdf_path.name}")
        print(f"Pages: {len(pages)}")
        print("-" * 60)
        print("METADATA:")
        for k, v in meta.items():
            print(f"  {k:10s}: {v}")
        print("-" * 60)
        print(f"SECTIONS DETECTED ({len(sections)}):")
        for name, idx in sections:
            print(f"  line {idx:5d}: {name}")
        print("=" * 60)
        return

    out_path = Path(args.output) if args.output else pdf_path.with_suffix(".md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path} ({len(md):,} chars, {len(sections)} sections)")


if __name__ == "__main__":
    main()
