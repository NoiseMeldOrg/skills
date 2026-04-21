# NoiseMeld Skills

Claude Code skills for extracting documents, editing prose, and explaining code. Built on the [Agent Skills](https://agentskills.io) open standard.

## Installation

### Plugin marketplace (recommended)

Register the marketplace in Claude Code:

```
/plugin marketplace add NoiseMeldOrg/skills
```

Install the skills you want:

```
/plugin install extract-book@noisemeld-skills
/plugin install extract-study@noisemeld-skills
/plugin install extract-transcript@noisemeld-skills
/plugin install extract-webpage@noisemeld-skills
/plugin install clear-and-concise-humanization@noisemeld-skills
/plugin install explain-code@noisemeld-skills
```

Or grab a bundle:

```
/plugin install extraction-skills@noisemeld-skills    # all four extract skills
/plugin install writing-skills@noisemeld-skills        # humanization + explain-code
```

Plugin skills are namespaced (`/noisemeld-skills:extract-book`) and available in every project.

### Manual install (no namespace)

Clone and symlink for shorter `/extract-book` names:

```bash
git clone https://github.com/NoiseMeldOrg/skills.git ~/skills

ln -s ~/skills/skills/extract-book ~/.claude/skills/
ln -s ~/skills/skills/extract-study ~/.claude/skills/
ln -s ~/skills/skills/extract-transcript ~/.claude/skills/
ln -s ~/skills/skills/extract-webpage ~/.claude/skills/
ln -s ~/skills/skills/clear-and-concise-humanization ~/.claude/skills/
ln -s ~/skills/skills/explain-code ~/.claude/skills/
```

Pull the repo to update. Symlinks pick up changes immediately.

### Project-level install

Add a skill to one project so your team gets it through version control:

```bash
ln -s ~/skills/skills/extract-study /path/to/project/.claude/skills/
```

### Python dependencies

The extract skills need Python packages:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pdfplumber youtube_transcript_api trafilatura
```

`extract-book` and `extract-study` use `pdfplumber`. `extract-transcript` uses `youtube_transcript_api` when fetching from YouTube URLs (pasted transcripts need nothing). `extract-webpage` uses `trafilatura` for fetching and content extraction.

---

## Skills

### extract-book

Converts a PDF book into Markdown with chapters, metadata, and cleaned text.

Give Claude a PDF path, or run `/extract-book path/to/book.pdf`. Claude starts with a dry run to preview detected chapters, reviews the results with you, then extracts and post-processes: fixes the auto-detected title, fills in any missing metadata, and handles image placeholders.

The bundled script detects chapters four ways: `CHAPTER N` text markers, bare number pages, ALL-CAPS section headers, and table-of-contents matching. It extracts author, publisher, copyright, and ISBN from the first pages and strips page numbers and watermarks.

Flags: `--dry-run` to preview, `--render-images` to capture image-heavy pages as PNGs, `-o path.md` to set the output path.

---

### extract-study

Converts a research paper PDF into Markdown with IMRaD sections, metadata, and references.

Give Claude a PDF (with an optional PubMed or DOI link for context), or run `/extract-study path/to/paper.pdf`. Claude runs a dry run, extracts, then verifies the title, authors, and DOI, writes 3-6 key findings bullets, and spot-checks tables for column-merge artifacts.

The script detects standard section headings (Abstract, Methods, Results, Discussion, Conclusion, References) and pulls DOI, PMID/PMCID, title, authors, journal, and year from the first pages.

Flags: `--dry-run` to preview, `--layout` for two-column PDFs, `--render-images` for figures and charts, `-o path.md` to set the output path.

---

### extract-transcript

Turns a YouTube video or podcast into a structured Markdown summary.

Give Claude a YouTube URL, paste a raw transcript, or run `/extract-transcript https://www.youtube.com/watch?v=XXXXX`. Claude fetches the transcript and video metadata automatically, reads through the full content, and writes an organized summary with sections, key quotes as blockquotes, and a source block with clickable links.

This is a reasoning task. Claude reorganizes messy spoken-word content into clear prose, preserving the speaker's arguments and evidence while cutting filler and repetition.

---

### extract-webpage

Extracts web pages into clean Markdown with navigation, ads, and boilerplate stripped out.

Give Claude a URL, or run `/extract-webpage https://example.com/article`. Claude runs a dry run to preview the detected metadata (title, author, date, word count), then extracts and post-processes: fixes the title, fills in missing metadata, and cleans up any boilerplate the script missed.

For full-site crawls, add `--crawl` to discover and extract all pages on the domain. The script finds pages via sitemap or link following, filters out tag/category/login pages by default, and combines everything into one document with a table of contents. Use `--max-pages` to cap the crawl and `--delay` to control request pacing.

The bundled script uses trafilatura for content extraction. It handles most static HTML sites well. JavaScript-rendered pages (React SPAs, heavy client-side rendering) and authenticated pages won't work -- the dry run shows this immediately (0 words extracted).

Flags: `--dry-run` to preview, `--crawl` for multi-page, `--max-pages N` to limit crawl, `--no-links` to strip hyperlinks, `--exclude /pattern/` to filter URLs, `--no-exclude` to disable default filtering.

---

### clear-and-concise-humanization

Edits prose so it reads as clear, direct, and human-written. Ten structured editing passes built on two foundations:

**Strunk's *Elements of Style*** -- active voice, omit needless words, concrete language, emphatic word placement. Full text in `references/elements-of-style/`.

**Wikipedia's "Signs of AI writing"** -- detection patterns from Wikipedia editors who review AI-generated submissions. Full article in `references/signs-of-ai-writing.md`.

Claude applies this skill automatically to prose writing tasks. You can also hand it a document and say "humanize this" or "clean up this draft."

The ten passes, in order:

1. **Structure** -- break uniform paragraphs, drop subheadings that don't earn their keep
2. **Significance inflation** -- delete "crucially," "it's worth noting," and empty importance claims
3. **Vocabulary** -- replace AI-overused words (delve, leverage, tapestry, multifaceted)
4. **Grammar** -- fix nominalizations, passive voice, copula stacking
5. **Rhythm** -- mix short and long sentences
6. **Hedging** -- cut "might potentially," "in essence," and doubled qualifiers
7. **Connective tissue** -- reduce em dashes, drop "Moreover/Furthermore/Additionally"
8. **Trailing participials** -- fix ", creating..." and ", enabling..." sentence endings
9. **Promotional language** -- cut "commitment to excellence," vague attributions, elegant variation
10. **Soul** -- add a specific, human detail where the piece needs it

Output includes a Changes table showing what each pass fixed. Only passes with actual changes appear.

This skill merges two open-source skills and three reference sources into one:

**Skills merged:**
- [**writing-clearly-and-concisely**](https://github.com/softaworks/agent-toolkit) by [@joshuadavidthomas](https://github.com/joshuadavidthomas) (via Softaworks agent-toolkit) -- Strunk's composition rules plus AI vocabulary pattern detection. MIT license.
- [**humanize-writing**](https://github.com/jpeggdev/humanize-writing) by [@jpeggdev](https://github.com/jpeggdev) -- eight-pass editing system for rewriting AI-generated prose. MIT license. Incorporates work from [blader/humanizer](https://github.com/blader/humanizer) (the "soul" pass philosophy and 24 Wikipedia-sourced detection patterns).

**Reference sources bundled:**
- [**The Elements of Style**](https://github.com/obra/the-elements-of-style) by William Strunk Jr. (1918, public domain) -- Markdown adaptation by [@obra](https://github.com/obra). Strunk rule citations are woven into each editing pass.
- [**Signs of AI writing**](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup) -- field guide maintained by Wikipedia's WikiProject AI Cleanup editors. Covers regression-to-the-mean theory, promotional language patterns, trailing participials, bold-header lists, and elegant variation.
- **AI-tell word lists** -- tiered vocabulary lists (Tier 1 red flags, Tier 2 cluster words) compiled from the above sources and extended with observed model-generation patterns.

The merge cut the overlap between writing-clearly-and-concisely and humanize-writing, expanded from 8 passes to 10, and threaded Strunk rule citations into each pass so the writing principles and the AI-tell detection reinforce each other.

---

### explain-code

Explains code with visual diagrams and everyday analogies.

Ask "how does this work?" or run `/explain-code path/to/file.ts`. Claude produces an analogy comparing the code to something familiar, an ASCII diagram of the flow or structure, a step-by-step walk-through, and a section on common mistakes.

No dependencies. Works with any language.

---

## Making skills trigger reliably

Claude tends to under-trigger skills. It knows they exist, but won't always reach for them unless you make the connection clear. Several things help.

### Write a good description

The `description` field in SKILL.md frontmatter is the primary trigger. Claude reads every installed skill's description at the start of each session to decide what's available. Front-load the key use case and list the phrases a user would actually say:

```yaml
description: >
  Convert PDF books into structured Markdown. Use when the user says
  "extract this book," "convert this PDF," "process this PDF," or
  drops a book PDF path.
```

Descriptions are truncated at 1,536 characters. Put the important information first.

### Add a `when_to_use` field

The `when_to_use` frontmatter field appends extra trigger phrases to the description. Use it for phrases you want Claude to match on without cluttering the main description:

```yaml
when_to_use: >
  Also trigger when the user mentions a book PDF, drops a PDF path
  that looks like a book (chapters, table of contents), or says
  "here's a book I want in markdown."
```

### Reference skills in CLAUDE.md

The most reliable way to make a skill fire is to mention it in your project or global CLAUDE.md. Claude reads CLAUDE.md at the start of every session and treats its contents as standing instructions:

```markdown
## Writing

When writing or editing prose, apply the `clear-and-concise-humanization` skill.
This includes drafting, revising, and any task producing more than a few sentences.
```

This works at both levels:
- **Global** (`~/.claude/CLAUDE.md`) -- applies across all projects
- **Project** (`.claude/CLAUDE.md` or `CLAUDE.md` at project root) -- applies to that project

### Use the `paths` field

Restrict a skill to fire only when working with certain file types:

```yaml
paths: "*.pdf, *.PDF"
```

This keeps the skill from loading in contexts where it isn't useful and makes it more likely to load when it is.

### Raise the description budget

If you have many skills installed and some descriptions are getting truncated, increase the character budget. Set this environment variable before starting Claude Code:

```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=16000
```

The default scales at 1% of the context window with a fallback of 8,000 characters.

### Invoke directly when needed

If Claude doesn't pick up a skill automatically, invoke it by name:

```
/extract-book path/to/book.pdf
```

Direct invocation always works, regardless of description matching. You can also ask Claude "what skills are available?" to see what it knows about.

---

## Updating

**Plugin install:** Run `/plugin marketplace add NoiseMeldOrg/skills` again to refresh, then reinstall.

**Manual install:** Pull the repo.

```bash
cd ~/skills && git pull
```

## License

MIT
