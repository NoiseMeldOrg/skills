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

Reuse `extract-book`'s `.venv` if it exists; otherwise create one in the working directory:

```bash
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate && python -c "import pdfplumber" 2>/dev/null || pip install pdfplumber
```

Don't suppress pip errors with `2>/dev/null` — surface them so missing toolchains (e.g. no Python build deps) fail loud rather than as a confusing `ModuleNotFoundError` on the next line.

## Process

### Step 0: Get a Local PDF (when given a PMC link, DOI, or PubMed URL)

The script only takes a local PDF path. It doesn't fetch anything itself. When the user drops a link instead of a file:

1. **DOI given directly:** resolve it first: `https://doi.org/<doi>` redirects to the publisher's article page, which usually has a working PDF/"printable version" link that isn't bot-gated.
2. **PMC link or PMCID given:** don't assume `pmc.ncbi.nlm.nih.gov/articles/PMC<id>/pdf/...` will download. NCBI now gates PMC PDF downloads behind a JavaScript proof-of-work challenge ("Preparing to download..." interstitial) that a plain fetch/curl/urllib request can't solve. It comes back as a small HTML page, not a PDF. Instead, look up the paper's DOI (the PMC article HTML page itself usually still loads fine and shows the DOI) and go to the publisher's site per step 1. The Europe PMC REST API (`https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=PMCID:PMC<id>&format=json&resultType=core`) is a reliable way to resolve a PMCID to its DOI and title without hitting the gate.
3. **PubMed URL given:** the PubMed page links out to the publisher and to PMC (if available). Same as above: prefer the publisher/DOI route.
4. **Download the PDF** via WebFetch, or `curl`/Python `urllib` in Bash if the environment allows outbound network calls (approve the permission prompt if one appears). Save it to a working path before running the script.
5. **If every automated route is blocked** (paywalled, captcha, no working link), ask the user to download the PDF manually and give you the local path. Don't guess at a URL pattern indefinitely.

### Step 1: Dry Run

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_study_pdf.py "<path-to-pdf>" --dry-run
```

This prints the detected metadata (title, year, DOI, PMID/PMCID) and the list of sections found. Authors and journal are not auto-detected — fill those in by hand from the PDF's first page after extraction. Review with the user before extracting.

If the dry run prints a `WARNING: detected N tokens that look like ... right-to-left order` line, one of the paper's tables (usually a correlation matrix) was extracted with reversed cells. Either rerun with `--layout` or plan to reconstruct that table from the published HTML — never ship the .md without fixing it.

### Step 2: Extract

```bash
source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_study_pdf.py "<path-to-pdf>" -o "<output-path>.md"
```

If `-o` is omitted, output goes next to the PDF.

### Step 3: Post-Process

After extraction, read the top of the file and verify:

1. **Title, authors, journal, year, DOI/PMID** are correct. The script auto-detects title, year, DOI, PMID, and PMCID — but skips authors and journal, which need manual fill-in from the first page. NIHMS author manuscripts (PMC preprints) bury the title under "HHS Public Access / Author manuscript / Pain Pract. ..." cover matter; the script filters those lines but always sanity-check the title against the PDF. If the PMID/PMCID is missing or unclear, look the paper up on PubMed/PMC by DOI and fill in by hand.
2. **Add a "Key findings" bullet list** at the top (3-6 bullets: design, n, primary result, hazard ratios / effect sizes, main conclusion). This is the value of having the paper in the repo — future-you can scan it in 10 seconds.
3. **Tables**: The script extracts text-layer tables as best it can, but two-column layouts frequently interleave table rows with adjacent body text. For studies where the main result is in a table (hazard ratios, confidence intervals, p-values), reconstruct tables as clean Markdown from the PDF.
4. **Spot-check Methods and Results** for column-merge artifacts. Watch for two adjacent section headings joined on one line ("Introduction Case Presentation"), table rows wrapped into running text, and references interleaved with body sections.
5. **References** should be intact at the bottom. Leave them — even if ugly, they're useful for follow-on lookups.

**When to do a full rewrite vs. patch:** For short case reports, letters, or editorials (≤6 pages, non-IMRaD), the extracted output often needs complete reorganization. In that case, read the PDF carefully and rewrite the Markdown from scratch using the target format below. A full rewrite in one pass is faster than patching dozens of column-bleed artifacts.

### Step 4: File it

**Location:** Ask the user where to save it unless the project's CLAUDE.md or an existing folder of study extractions makes it obvious. Match the filing pattern of neighboring studies if there is one.

**Filename:** Lowercase kebab-case — `<firstauthor>-<year>-<short-slug>.md`.

- **`<firstauthor>`** is the first author's surname only (strip initials and "et al"). "Dugani SB" → `dugani`.
- **`<year>`** is the publication year.
- **`<short-slug>`** is a 3–6 word descriptive title. Keep the full paper title in the `# H1` heading inside the file.
- **Normalize names:** strip to ASCII, lowercase, drop apostrophes/accents. "O'Brien" → `obrien`, "Mendoza-López" → `mendoza-lopez`.

Example: `dugani-2021-lipid-markers-womens-health.md`.

**PDF handling:** Rename the source PDF to match the Markdown filename exactly (same kebab slug, same directory, `.pdf` extension) so the PDF and MD are paired and discoverable under one search. Use `git mv` if the PDF is already tracked.

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
- **Acknowledgments** / Acknowledgements
- **Funding** / Funding Information
- **Conflicts of Interest** / Competing Interests
- **Data Availability** (statement)
- **What is Known** / **What This Study Adds** (sidebar boxes common in BMJ-style journals)
- **References** / Bibliography / Literature Cited

Headings can be in ALL CAPS, Title Case, or numbered (`1. Introduction`, `2. Methods`). The script normalizes them to `## Section Name`. Anything before the first detected section becomes the metadata block + abstract area; anything after References stays under References.

## Troubleshooting

- **Two-column bleed**: pdfplumber usually handles columns well, but some journals (older Cureus, some Elsevier, JCEM Case Reports) interleave. If Methods/Results look scrambled, rerun with `--layout` (uses pdfplumber's layout=True mode). For very short papers (≤6 pages), a full manual rewrite from the PDF is usually faster than patching bleed artifacts. `--layout` is not a sure fix. On some PDFs it leaves the bleed unchanged and adds odd multi-space gaps to the extracted title; check the dry-run title again after retrying with it, and fall back to a manual rewrite if it didn't help.
- **Words run together with no spaces**: A minority of PDFs (seen in some PLOS ONE exports) have a text layer where pdfplumber can't find inter-word gaps at all, so the whole body reads like "ofAgriculturalResearchHoleta...". Neither default mode nor `--layout` fixes this. It's the PDF's own character-spacing metadata, not a script bug. Section headings glued into running text this way won't be detected either. Pull the paper from the publisher's HTML version if one exists, or do a full manual rewrite.
- **Reversed table cells (right-to-left)**: Some PDFs encode correlation matrices with reversed text direction, so cells like `0.28**` come out as `**82.0` and labels like `CSI` come out as `ISC`. The script detects this and prints a warning at extraction time. Fix by either retrying with `--layout` or pulling the table straight from the published HTML (PMC or the journal site) and pasting it in.
- **NIHMS / PMC author manuscripts**: For papers retrieved from PMC under their NIHMS preprint number (`nihms-XXXXXX.pdf`), the PDF puts "HHS Public Access / Author manuscript" cover matter and a running journal cite ahead of the title. The script filters this chrome, but always cross-check the .md against the **PMC HTML** page (`pmc.ncbi.nlm.nih.gov/articles/PMC<id>/`) — it gives you a clean Table 2, intact references with PubMed links, and verified PMID. Make this a default step for any NIHMS-prefixed PDF.
- **Title pollution**: On journals that use a running header on page 1 (e.g. "JCEM Case Reports, 2024, 2, luae102 Advance access publication 10 July 2024..."), older versions of the script concatenated the header with the actual title. The script now filters NIHMS and "Published in final edited form as" lines and stitches multi-line titles (including hyphenated breaks like `cross-` + `sectional`), but unfamiliar journal-specific cover matter can still leak through — sanity-check the title.
- **Authors/journal not detected**: Multi-line author blocks with superscript affiliations frequently fail detection. Read the first page and fill in manually.
- **Missing DOI**: Regex looks for `10.xxxx/...` patterns. If the paper uses an unusual DOI format, add it manually.
- **No sections detected**: Short letters, editorials, and case reports sometimes lack IMRaD structure. The script falls back to a flat extraction — add headings manually or do a full rewrite.
- **Garbled references**: Reference lists with heavy formatting (superscripts, special chars) can extract poorly. Consider pulling the reference list from the PMC HTML page instead.
- **Cross-reference related docs**: If the study was discussed in a video transcript already filed in the repo, add a "see also" link in the Markdown and a "Published paper" field in the transcript summary. Cross-references keep the transcript + study pair discoverable together.
