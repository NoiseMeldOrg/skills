# NoiseMeld Skills

Custom [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for document extraction, writing, and code explanation. Built on the [Agent Skills](https://agentskills.io) open standard.

## Installation

### Plugin marketplace (recommended)

Register the marketplace in Claude Code:

```
/plugin marketplace add NoiseMeldOrg/skills
```

Install individual skills:

```
/plugin install extract-book@noisemeld-skills
/plugin install extract-study@noisemeld-skills
/plugin install extract-transcript@noisemeld-skills
/plugin install clear-and-concise-humanization@noisemeld-skills
/plugin install explain-code@noisemeld-skills
```

Or install bundles:

```
/plugin install extraction-skills@noisemeld-skills    # all three extract skills
/plugin install writing-skills@noisemeld-skills        # humanization + explain-code
```

Plugin skills are namespaced: `/noisemeld-skills:extract-book`. They work across all projects.

### Manual install (no namespace)

For shorter `/extract-book` names, clone and symlink into your global skills directory:

```bash
git clone https://github.com/NoiseMeldOrg/skills.git ~/skills

# Symlink whichever skills you want
ln -s ~/skills/skills/extract-book ~/.claude/skills/
ln -s ~/skills/skills/extract-study ~/.claude/skills/
ln -s ~/skills/skills/extract-transcript ~/.claude/skills/
ln -s ~/skills/skills/clear-and-concise-humanization ~/.claude/skills/
ln -s ~/skills/skills/explain-code ~/.claude/skills/
```

To update later, pull the repo. Symlinks pick up changes automatically.

### Project-level install

To add skills to a single project (checked into version control so your team gets them too):

```bash
ln -s ~/skills/skills/extract-study /path/to/project/.claude/skills/
```

### Python dependencies

The three extract skills require Python packages. Set up a venv in each project where you use them:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pdfplumber youtube_transcript_api
```

`extract-book` and `extract-study` need `pdfplumber`. `extract-transcript` needs `youtube_transcript_api` (only when fetching from YouTube URLs; pasted transcripts need nothing).

---

## Skills

### extract-book

Convert a PDF book into structured Markdown with chapters, metadata, and cleaned text.

**Invoke:** Give Claude a PDF path, or run `/extract-book path/to/book.pdf`

**What it does:**
1. Detects chapters using four strategies (text markers, single numbers, section headers, TOC matching)
2. Extracts metadata (title, author, publisher, copyright, ISBN) from the first pages
3. Optionally renders image-heavy pages as PNGs for a vision pass
4. Produces a Markdown file with `# Title`, labeled metadata block, `## Chapter` headings, and cleaned body text

**Options:**
- `--dry-run` -- preview detected chapters and metadata without writing
- `--render-images` -- render pages with little extractable text as PNGs
- `-o path.md` -- specify output path (default: same name as PDF)

**Example:**
```
Here's a book PDF I'd like extracted: archive/docs/books/Lies My Doctor Told Me - Dr Ken Berry.pdf
```

Claude runs a dry run first, reviews the detection with you, then extracts and post-processes (fixing title, filling missing metadata, handling image placeholders).

---

### extract-study

Convert a research paper PDF into structured Markdown with IMRaD sections, metadata, and references.

**Invoke:** Give Claude a PDF path or a PubMed/DOI link plus the PDF, or run `/extract-study path/to/paper.pdf`

**What it does:**
1. Detects IMRaD section headings (Abstract, Methods, Results, Discussion, Conclusion, References)
2. Extracts DOI, PMID/PMCID, title, authors, journal, and year from the first pages
3. Produces a Markdown file with a metadata header, key findings bullets, section structure, and preserved reference list

**Options:**
- `--dry-run` -- preview detected metadata and sections
- `--layout` -- use pdfplumber's layout mode for two-column PDFs
- `--render-images` -- capture figures and charts as PNGs
- `-o path.md` -- specify output path

**Example:**
```
/extract-study ~/Downloads/ridker-2024-nejm.pdf
```

Claude runs a dry run, extracts, then post-processes: verifies title/authors/DOI, adds 3-6 key findings bullets, spot-checks tables and column-merged text.

---

### extract-transcript

Convert a YouTube video or podcast transcript into a structured Markdown summary.

**Invoke:** Give Claude a YouTube URL, paste a raw transcript, or run `/extract-transcript https://www.youtube.com/watch?v=XXXXX`

**What it does:**
1. Fetches the transcript from YouTube (or accepts pasted text)
2. Fetches video title and channel via YouTube's oembed API
3. Reads the full transcript, identifies the core argument and natural section breaks
4. Produces a structured summary (not a raw transcription) with metadata, organized sections, key quotes as blockquotes, and a source block with clickable links

**Example:**
```
/extract-transcript https://www.youtube.com/watch?v=QpCRjS732uE
```

This is a reasoning task, not reformatting. Claude reorganizes messy spoken-word content into clear prose, preserving the speaker's arguments and evidence while cutting filler and repetition.

---

### clear-and-concise-humanization

Edit prose so it reads as clear, forceful, and human-written. Ten structured passes that combine two foundations:

1. **Strunk's *Elements of Style*** -- active voice, omit needless words, concrete language, emphatic placement. Full text in `references/elements-of-style/`.
2. **Wikipedia's "Signs of AI writing"** -- detection patterns from Wikipedia editors who review AI-generated submissions. Full article in `references/signs-of-ai-writing.md`.

**Invoke:** Claude applies this automatically to any prose writing task. You can also hand it a document: "humanize this" or "clean up this draft."

**The ten passes:**
1. Structure -- break uniform paragraphs, kill unnecessary subheadings
2. Significance inflation -- delete "crucially," "it's worth noting," empty importance claims
3. Vocabulary -- replace AI-overused words (delve, leverage, tapestry, multifaceted)
4. Grammar patterns -- fix nominalizations, passive voice, copula stacking
5. Rhythm and sentence variety -- mix short and long sentences
6. Hedging and filler -- cut defensive reflexes ("might potentially," "in essence")
7. Connective tissue -- reduce em dashes, kill "Moreover/Furthermore/Additionally"
8. Trailing participials -- fix ", creating..." / ", enabling..." sentence endings
9. Promotional language -- cut "commitment to excellence," vague attributions, elegant variation
10. Soul -- add one or two specific, human details

**Output:** The edited prose plus a Changes table showing what each pass fixed.

**Background:** This skill merges two earlier skills (`writing-clearly-and-concisely` for Strunk's rules and a separate humanization pass system) with the Wikipedia AI detection research as a third input.

---

### explain-code

Explain code using visual diagrams and everyday analogies.

**Invoke:** Ask "how does this work?" or run `/explain-code path/to/file.ts`

**What it produces:**
1. An everyday analogy comparing the code to something familiar
2. An ASCII diagram showing the flow, structure, or relationships
3. A step-by-step walk-through of what the code does
4. A gotcha section highlighting common mistakes or misconceptions

No dependencies. Works with any language.

---

## Updating

**Plugin install:** Run `/plugin marketplace add NoiseMeldOrg/skills` again to refresh, then reinstall the plugins you want.

**Manual install:** Pull the repo. Symlinks pick up changes immediately.

```bash
cd ~/skills && git pull
```

## License

MIT
