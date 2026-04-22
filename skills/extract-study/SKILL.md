---
name: extract-study
description: >
  This skill should be used when the user asks to "extract a study", "convert this paper",
  "process this journal article", or drops a PMC link, DOI, PubMed URL, or research PDF into
  the conversation. Handles anything from PubMed/PMC, NEJM, JAMA, Lancet, JACC, Cureus, Nature,
  etc. Specifically for papers with IMRaD structure (Abstract, Methods, Results, Discussion),
  not books. Also triggers when the user mentions a study PDF without explicitly asking to convert it.
---

# Extract Study PDF to Structured Markdown

Convert research papers into clean Markdown with a metadata header, IMRaD section structure, and preserved references. The bundled Python script handles two-column layouts, section detection, and metadata extraction automatically.

## When to Use

- User has a study/paper PDF they want in Markdown
- User drops a PMC, PubMed, or DOI link and a PDF path
- User wants to add a paper to a project for reference
- User has an existing extraction that's missing metadata or section structure

## Setup

Same venv as `extract-book`:

```bash
source .venv/bin/activate && pip install pdfplumber 2>/dev/null
```

## Process

### Step 1: Dry Run

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_study_pdf.py "<path-to-pdf>" --dry-run
```

This prints the detected metadata (title, year, DOI, PMID/PMCID) and the list of sections found. Authors and journal are not auto-detected — fill those in by hand from the PDF's first page after extraction. Review with the user before extracting.

### Step 2: Extract

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_study_pdf.py "<path-to-pdf>" -o "<output-path>.md"
```

If `-o` is omitted, output goes next to the PDF.

### Step 3: Post-Process

After extraction, read the top of the file and verify:

1. **Title, authors, journal, year, DOI/PMID** are correct. The script often munges multi-line cover matter into the title field (journal header + publication date + title all concatenated). Always check the first page of the PDF and rewrite the title, author list, and journal field cleanly. Check the DOI landing page if anything is unclear.
2. **Add a "Key findings" bullet list** at the top (3-6 bullets: design, n, primary result, hazard ratios / effect sizes, main conclusion). This is the value of having the paper in the repo — future-you can scan it in 10 seconds.
3. **Tables**: The script extracts text-layer tables as best it can, but two-column layouts frequently interleave table rows with adjacent body text. For studies where the main result is in a table (hazard ratios, confidence intervals, p-values), reconstruct tables as clean Markdown from the PDF.
4. **Spot-check Methods and Results** for column-merge artifacts. Watch for two adjacent section headings joined on one line ("Introduction Case Presentation"), table rows wrapped into running text, and references interleaved with body sections.
5. **References** should be intact at the bottom. Leave them — even if ugly, they're useful for follow-on lookups.

**When to do a full rewrite vs. patch:** For short case reports, letters, or editorials (≤6 pages, non-IMRaD), the extracted output often needs complete reorganization. In that case, read the PDF carefully and rewrite the Markdown from scratch using the target format below. A full rewrite in one pass is faster than patching dozens of column-bleed artifacts.

### Step 4: File it

**Location:** Ask the user where to save it unless the project's CLAUDE.md or an existing folder of study extractions makes it obvious. Match the filing pattern of neighboring studies if there is one.

**Filename:** A reasonable default is `<FirstAuthor> <Year> - <Short Title>.md` (e.g., `Dugani 2021 - Lipid Markers Women's Health Study.md`).

**PDF handling:** Rename the source PDF to match the Markdown filename exactly (same short title, same directory) so the PDF and MD are paired and discoverable under one search. Use `git mv` if the PDF is already tracked.

## Target Output Format

```markdown
# [Paper Title]

**Authors:** [First Author], [Second Author], et al.
**Journal:** [Journal Name]
**Year:** [Year]
**DOI:** [DOI]
**PMID/PMCID:** [if known]
**Study design:** [RCT / cohort / meta-analysis / etc. — fill in manually if not obvious]

## Key Findings

- [bullet 1]
- [bullet 2]
- ...

---

## Abstract

[extracted text]

## Background / Introduction

[extracted text]

## Methods

[extracted text]

## Results

[extracted text]

## Discussion

[extracted text]

## Conclusion

[extracted text]

---

## References

[preserved reference list]
```

## How Section Detection Works

The script scans for IMRaD-style headings at the start of lines. It recognizes common variants:

- **Abstract** / Summary
- **Introduction** / Background
- **Methods** / Materials and Methods / Methodology / Patients and Methods / Study Design
- **Results** / Findings
- **Discussion**
- **Conclusion** / Conclusions
- **References** / Bibliography / Literature Cited

Headings can be in ALL CAPS, Title Case, or numbered (`1. Introduction`, `2. Methods`). The script normalizes them to `## Section Name`. Anything before the first detected section becomes the metadata block + abstract area; anything after References stays under References.

## Troubleshooting

- **Two-column bleed**: pdfplumber usually handles columns well, but some journals (older Cureus, some Elsevier, JCEM Case Reports) interleave. If Methods/Results look scrambled, rerun with `--layout` (uses pdfplumber's layout=True mode). For very short papers (≤6 pages), a full manual rewrite from the PDF is usually faster than patching bleed artifacts.
- **Title pollution**: On journals that use a running header on page 1 ("JCEM Case Reports, 2024, 2, luae102 Advance access publication 10 July 2024..."), the script often concatenates the header with the actual title. Always rewrite the title cleanly — do not ship the extracted title field unedited.
- **Authors/journal not detected**: Multi-line author blocks with superscript affiliations frequently fail detection. Read the first page and fill in manually.
- **Missing DOI**: Regex looks for `10.xxxx/...` patterns. If the paper uses an unusual DOI format, add it manually.
- **No sections detected**: Short letters, editorials, and case reports sometimes lack IMRaD structure. The script falls back to a flat extraction — add headings manually or do a full rewrite.
- **Garbled references**: Reference lists with heavy formatting (superscripts, special chars) can extract poorly. Consider pulling the reference list from the PMC HTML page instead.
- **Cross-reference related docs**: If the study was discussed in a video transcript already filed in the repo, add a "see also" link in the Markdown and a "Published paper" field in the transcript summary. Cross-references keep the transcript + study pair discoverable together.
