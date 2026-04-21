# Skills

Custom [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for document extraction, writing, and code explanation. Follows the [Agent Skills](https://agentskills.io) open standard.

## Installation

### Plugin marketplace (recommended)

In Claude Code, run:

```
/plugin marketplace add NoiseMeldOrg/skills
```

Then install individual skills or bundles:

```
# Individual skills
/plugin install clear-and-concise-humanization@noisemeld-skills
/plugin install extract-book@noisemeld-skills
/plugin install extract-study@noisemeld-skills
/plugin install extract-transcript@noisemeld-skills
/plugin install explain-code@noisemeld-skills

# Or install bundles
/plugin install writing-skills@noisemeld-skills
/plugin install extraction-skills@noisemeld-skills
```

Skills installed this way are namespaced (e.g., `/noisemeld-skills:extract-book`). They work across all your projects automatically.

### Manual (global, no namespace)

Clone and symlink into your personal skills directory for shorter `/extract-book` style names:

```bash
git clone https://github.com/NoiseMeldOrg/skills.git ~/Source/Repos/NoiseMeldOrg/skills

# Symlink individual skills
ln -s ~/Source/Repos/NoiseMeldOrg/skills/skills/clear-and-concise-humanization ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/skills/explain-code ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/skills/extract-book ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/skills/extract-study ~/.claude/skills/
ln -s ~/Source/Repos/NoiseMeldOrg/skills/skills/extract-transcript ~/.claude/skills/
```

### Dependencies

The extract skills require Python packages. Set up a virtual environment in each project where you use them:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pdfplumber youtube_transcript_api
```

## Skill sets

### writing-skills

**clear-and-concise-humanization** -- Write and edit prose that is clear, forceful, and unrecognizable as machine-generated. Ten structured editing passes built on two foundations:

1. William Strunk Jr.'s *The Elements of Style* (1918) -- the composition rules (active voice, omit needless words, concrete language, emphatic placement). Full text in `references/elements-of-style/`.

2. Wikipedia's "Signs of AI writing" research -- detection patterns developed by Wikipedia editors to identify AI-generated submissions. Full article in `references/signs-of-ai-writing.md`. Key patterns: regression to statistical means, trailing participial clauses, bold-header list format, elegant variation, promotional language.

This skill is a merged and rewritten combination of two earlier skills (`writing-clearly-and-concisely` for Strunk's rules, and a separate humanization pass system) plus the Wikipedia AI detection research as a third input.

**explain-code** -- Explains code with visual ASCII diagrams and everyday analogies. Walks through the code step by step and highlights common gotchas.

### extraction-skills

**extract-book** -- Converts PDF books into structured Markdown with chapter detection, metadata extraction (author, publisher, ISBN, copyright), and image-page rendering for a vision pass. The bundled script tries four chapter-detection strategies: text markers, single-number chapters, section headers, and TOC-based matching. Requires `pdfplumber`.

**extract-study** -- Converts research papers (IMRaD format) into structured Markdown with a metadata header, section detection, and preserved references. Auto-detects DOI, PMID/PMCID, and standard section headings. Requires `pdfplumber`.

**extract-transcript** -- Converts video and podcast transcripts into structured Markdown summaries. Accepts YouTube URLs (fetches transcript automatically) or pasted raw transcript text. Produces a metadata header, organized sections, and a source block with clickable links. Requires `youtube_transcript_api`.

## License

MIT
