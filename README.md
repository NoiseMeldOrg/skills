# Skills

Custom [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for document extraction, writing, and code explanation.

## Skills

### clear-and-concise-humanization

Write and edit prose that is clear, forceful, and unrecognizable as machine-generated. Ten structured editing passes built on two foundations:

1. **William Strunk Jr.'s *The Elements of Style* (1918)** -- the composition rules (active voice, omit needless words, concrete language, emphatic placement). The `references/elements-of-style/` directory contains the full text organized by chapter.

2. **Wikipedia's "Signs of AI writing" research** -- detection patterns developed by Wikipedia editors to identify AI-generated submissions. The full article is in `references/signs-of-ai-writing.md`. Key patterns include regression to statistical means, trailing participial clauses, bold-header list format, elegant variation, and promotional language.

This skill is a merged and rewritten combination of two earlier skills:
- `writing-clearly-and-concisely` (Strunk's rules applied to technical and professional writing)
- A humanization pass system (ten-pass editing framework targeting specific AI tells)

The merge eliminated overlap between the two and added the Wikipedia AI detection research as a third input, producing a single skill that handles both clear writing and AI-tell removal in one workflow.

### explain-code

Explains code with visual ASCII diagrams and everyday analogies. Walks through the code step by step and highlights common gotchas.

### extract-book

Converts PDF books into structured Markdown with chapter detection, metadata extraction (author, publisher, ISBN, copyright), and image-page rendering for a vision pass. The bundled Python script (`scripts/extract_book_pdf.py`) tries four chapter-detection strategies automatically: text markers, single-number chapters, section headers, and TOC-based matching.

Requires `pdfplumber`.

### extract-study

Converts research papers (IMRaD format) into structured Markdown with a metadata header, section detection, and preserved references. The bundled script (`scripts/extract_study_pdf.py`) auto-detects DOI, PMID/PMCID, and standard section headings.

Requires `pdfplumber`.

### extract-transcript

Converts video and podcast transcripts into structured Markdown summaries. Accepts YouTube URLs (fetches transcript automatically via `tools/get_transcript.py`) or pasted raw transcript text. Produces a metadata header, organized sections, and a source block with clickable links.

Requires `youtube_transcript_api`.

## Installation

Clone this repo, then symlink the skills you want into your Claude Code skills directory:

```bash
# Clone
git clone https://github.com/NoiseMeldOrg/skills.git ~/Source/Repos/NoiseMeldOrg/skills

# Install globally (available in all projects)
ln -s ~/Source/Repos/NoiseMeldOrg/skills/clear-and-concise-humanization ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/explain-code ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/extract-book ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/extract-study ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/extract-transcript ~/.claude/skills/

# Or install into a specific project
ln -s ~/Source/Repos/NoiseMeldOrg/skills/extract-book /path/to/project/.claude/skills/
```

For the extract skills, set up a Python virtual environment in the project where you use them:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pdfplumber youtube_transcript_api
```

## License

MIT
