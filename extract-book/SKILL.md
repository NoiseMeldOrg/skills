---
name: extract-book
description: >
  This skill should be used when the user asks to "convert a PDF book to Markdown", "extract a book",
  "process this PDF", or has PDF books to organize or make searchable. Also triggers when the user
  mentions a book PDF or drops a PDF path that appears to be a book (chapters, table of contents,
  forewords). Specifically for books, not papers or short documents. If it has an Abstract and
  References section, use extract-study instead.
---

# Extract Book PDF to Structured Markdown

Convert PDF books into well-structured Markdown files with proper chapter headings, metadata blocks, horizontal rule dividers, and cleaned text. The bundled Python script handles chapter detection automatically using multiple strategies.

## When to Use

- User wants to convert a PDF book to Markdown
- User has a collection of PDF books to process
- User has existing Markdown book extractions that lack chapter structure
- User mentions a book PDF and wants it readable/searchable

## Setup (one-time per project)

The script requires Python 3.10+ and the `pdfplumber` library. Set up a virtual environment if one doesn't already exist:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install pdfplumber
```

If `.venv` already exists, just activate and ensure pdfplumber is installed:
```bash
source .venv/bin/activate && pip install pdfplumber 2>/dev/null
```

Add `.venv/` to `.gitignore` if it's not already there.

## Process

### Step 1: Dry Run

Always start with `--dry-run` to preview what the script detects before writing output:

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_book_pdf.py "<path-to-pdf>" --dry-run
```

This prints:
- Which detection strategy was used
- How many chapters/sections were found
- The page ranges and titles for each section

### Step 2: Review with the User

Show the dry-run output and check:
- **Are all chapters detected?** Compare the detected list with the actual book structure.
- **Is the title correct?** Auto-detection sometimes grabs the wrong line (disclaimers, TOC headers). You'll fix this manually if needed.
- **Are there duplicates?** Endnotes sections sometimes repeat "Chapter N" — the script filters these, but verify.
- **For workbook/guidebook formats**: The script falls back to section-header detection. Verify the sections make sense.

### Step 3: Extract

Run with `--render-images` to capture image-based pages (chapter titles, diagrams, charts, tables rendered as images):

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_book_pdf.py "<path-to-pdf>" --render-images -o "<output-path>.md"
```

This does two things:
- Extracts text from all pages using pdfplumber
- Renders pages with little/no extractable text as PNG images to `.tmp/extracted_images/<book>/`
- Inserts `<!-- IMAGE: path | Page N — ... -->` placeholders in the Markdown where those pages appear

If `-o` is not specified, the output goes next to the PDF with the same name and `.md` extension.

If the user doesn't need image processing, omit `--render-images` for a text-only extraction (faster, no image files generated).

### Step 4: Vision Pass

After extraction, search the output for `<!-- IMAGE:` placeholders. For each one:

1. **Read the image** using the Read tool (Claude Code can read PNG files natively)
2. **Determine what the page contains:**
   - **Section/chapter title page** (decorative image with a title): Note the title text. If it matches the `##` heading above, delete the placeholder. If it provides a better title, update the heading.
   - **Table or chart**: Recreate it as a Markdown table. Add a caption line like `**Figure N:** [description]`
   - **Diagram or illustration**: Write a concise description of what it shows
   - **Scanned text page**: Transcribe the text content
   - **Purely decorative page** (stock photos, blank pages, ad pages): Delete the placeholder entirely
3. **Replace the placeholder** with the appropriate content using the Edit tool

Work through placeholders in order, batch-reading images when they're adjacent. For books with many image pages (50+), ask the user if they want to process all of them or just the important ones (chapter titles, tables, charts).

### Step 5: Post-Process

After the vision pass, read the first 20-30 lines of the output and fix:

1. **Title**: If auto-detected title is wrong (common with books that have disclaimer pages first), edit the `# Title` line to the actual book title with subtitle.
2. **Source metadata block**: Every book extraction must have a complete metadata block immediately below the title. The script auto-detects what it can, but many PDFs lack structured copyright pages. Fill in any gaps manually — check the PDF's first few pages, or look up the book online if needed. The required fields are:
   - **Author** (name and credentials)
   - **Publisher** (publisher name)
   - **Copyright** (year)
   - **ISBN** (ISBN-13 preferred)
   
   If the script missed any of these, add them by hand. A book extraction without at least author, copyright year, and ISBN is incomplete.
3. **Spot-check a chapter transition**: Read around a `## Chapter` heading to verify content flows correctly and there's no bleed from the previous chapter.
4. **Verify no placeholders remain**: Search for `<!-- IMAGE:` to confirm all were processed.

### Step 6: File It

**Location:** Books live in `archive/docs/books/` regardless of topic. Topic-specific subdirs are not used for books in this repo.

**Filename:** Use `<Title> - <Author>.md` with a clean, human-readable title (e.g., `Toxic Superfoods - Sally K Norton.md`, `Fix Your Diet Fix Your Life - Dr Ken Berry.md`). Drop subtitles from the filename if the title is long; keep the full title + subtitle inside the `# H1` heading.

**PDF handling:** Rename the source PDF to match the Markdown filename exactly (same title, same directory) so the pair is discoverable under a single search. Historical files in this repo include `_OceanofPDF.com_<Title>_-_<Author>.pdf` naming — when processing a new book, do a `git mv` to the clean `<Title> - <Author>.pdf` form to match the MD and match the newer convention. The `.gitignore` already excludes `._*` macOS metadata siblings.

### Step 7: Cross-Reference Related Docs

If the book references or is referenced by other material in the repo:

1. **Studies the book cites heavily** — if a cited study is already in `archive/docs/studies/`, add a reference link in the book's front matter or relevant chapter.
2. **Video transcripts by the same author** — add "See also" links pointing to their transcripts in `archive/docs/cardiovascular/videos/` (or the relevant topic subdir).
3. **Reference docs that draw on the book** — when a protocol or reference doc leans on the book, link both directions so the source is traceable.

### Step 8: Commit

Add and commit with a descriptive message.

## Target Output Format

```markdown
# Book Title: Subtitle

**Author:** Author Name, Credentials
**Publisher:** Publisher Name
**Copyright:** Copyright © Year
**ISBN:** 978-x-xxxxxx-xx-x
**Edition:** [if applicable]

---

## Foreword by [Name]

[extracted text]

---

## Chapter 1: Chapter Title Here

[extracted text]

---

## Chapter 2: Next Chapter Title

[extracted text]

---
```

The metadata block uses labeled fields (like extract-study and extract-transcript) so every book in the repo has a consistent, scannable header. The script outputs these fields automatically when it can detect them from the PDF. Fields the script misses must be filled in during post-processing.

## How Chapter Detection Works

The script tries four strategies in order, using the first one that finds 3+ chapters:

1. **Text markers** — Scans for `CHAPTER N` or `Chapter N:` patterns at the start of pages. Most common in traditionally formatted books.

2. **Single-number chapters** — Some publishers (e.g., Simon & Schuster) mark chapters with just a bare number (`1`, `2`, `3`) as the first line. The script validates these are sequential.

3. **Section headers** — For workbook-style books without traditional chapters. Detects ALL-CAPS headers. If there are too many (>25), keeps only multi-page sections.

4. **TOC-based sections** — For guidebooks. Parses the Table of Contents, then fuzzy-matches each entry to actual page content.

Additionally, the script always detects:
- **Named sections**: Foreword, Introduction, Epilogue, Acknowledgments, etc.
- **Part markers**: `Part 1`, `Part II`, etc.
- **Backmatter boundary**: Stops chapter detection when it hits Notes/Bibliography/References past the halfway point, preventing endnote citations from being detected as chapters.

## Automatic Text Cleanup

- Strips standalone page numbers (1-4 digit numbers alone on a line)
- Removes `OceanofPDF.com` watermark lines
- Removes duplicate chapter headers from body text (since they're already in `##` headings)
- Collapses excessive blank lines

## Batch Processing

To process multiple PDFs in a directory:

```bash
source .venv/bin/activate
for pdf in /path/to/pdfs/*.pdf; do
  python {SKILL_DIR}/scripts/extract_book_pdf.py "$pdf" --dry-run
done
```

Review the dry runs, then run without `--dry-run` for the ones that look good. Books with tricky formats may need the output path specified with `-o`.

## Troubleshooting

- **FontBBox warnings**: Harmless pdfplumber/pdfminer warnings. Ignore them.
- **No chapters detected**: The book may use an unusual format. Check `--dry-run` output and consider running the script to get a flat extraction, then manually add `## Chapter` headings.
- **Wrong title**: Very common. The script skips disclaimers and legal text but sometimes grabs the wrong line. Just edit the `# Title` line manually after extraction.
- **Chapters from endnotes**: The backmatter detector should catch this, but if not, the endnotes section may have lines like "Chapter 3: Smith et al..." that get detected. Run `--dry-run` to verify before extracting.
