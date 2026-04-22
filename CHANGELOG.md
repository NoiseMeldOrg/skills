# Changelog

Version `1.0.N` = the Nth commit on `main`. To check out any version:

```bash
git log --oneline main   # find the commit
git checkout <hash>      # check it out
```

## 1.0.12

Prepare skills for public release

- - Strip personal medical case from extract-transcript SKILL; relevance
- section is now opt-in via project CLAUDE.md
- - Genericize archive/docs filing paths in all four extract skills
- - Drop --render-images claim from extract-study (script never implemented)
- - Soften extract-study metadata claim: authors and journal are manual
- - Fix extract-webpage TOC anchors with a GitHub-compatible slugify
- - Add CLAUDE.md describing the marketplace, automation, and hook setup

## 1.0.11

Remove explain-code skill in favor of third-party version

- The third-party explain-code skill (zbruhnke/claude-code-starter) is more
- rigorous with anti-hallucination rules, structured output, and execution
- tracing. Removed our lighter version and the now-redundant writing-skills
- bundle from the marketplace.

## 1.0.10

Auto-generate CHANGELOG from git log via commit-msg hook

- CHANGELOG.md is now built from commit history at commit time.
- The commit-msg hook includes the current commit's message, so the
- CHANGELOG is never behind the actual version. Replaces the manually
- maintained CHANGELOG.

## 1.0.9

Add auto-versioning from git commit count and CHANGELOG

- Version 1.0.N = Nth commit on main, matching rapture-ios scheme.
- Pre-commit hook updates marketplace.json automatically. Documents
- update workflow for plugin marketplace and symlink users.

## 1.0.8

Expand clear-and-concise-humanization provenance with all sources

- Credits obra/the-elements-of-style (Strunk text), Wikipedia's
- WikiProject AI Cleanup (signs-of-ai-writing field guide), and
- blader/humanizer (soul pass) alongside the two primary skills.

## 1.0.7

Credit source skills for clear-and-concise-humanization

- Adds proper attribution to writing-clearly-and-concisely
- (joshuadavidthomas/softaworks) and humanize-writing (jpeggdev),
- both MIT licensed.

## 1.0.6

Add extract-webpage skill for web page to Markdown conversion

- Bundled Python script uses trafilatura for content extraction with
- automatic boilerplate removal. Supports single-page and multi-page
- site crawls. Updated marketplace.json and extraction-skills bundle.

## 1.0.5

Rewrite README: humanize prose, add skill invocation guidance

- Applied clear-and-concise-humanization passes to the documentation.
- Added "Making skills trigger reliably" section covering description
- optimization, when_to_use, CLAUDE.md references, paths field,
- description budget, and direct invocation.

## 1.0.4

Document installation methods and per-skill usage

- README now covers:
- - Three install methods (plugin marketplace, global symlink, project-level)
- - Python dependency setup
- - Per-skill documentation with invoke patterns, options, and examples
- - Update instructions for both install methods

## 1.0.3

Allow individual skill installation alongside bundles

- Each skill is now its own installable plugin in the marketplace.
- Bundles (writing-skills, extraction-skills) still available for
- installing groups at once.

## 1.0.2

Add plugin marketplace support and restructure to official pattern

- Restructured to match anthropics/skills convention:
- - Skills moved under skills/ directory
- - Added .claude-plugin/marketplace.json for plugin install support
- - Two plugin groups: writing-skills and extraction-skills
- - Updated README with plugin marketplace install instructions
- - Added MIT license
- Users can now install via:
- /plugin marketplace add NoiseMeldOrg/skills
- /plugin install writing-skills@noisemeld-skills

## 1.0.1

Initial commit: five custom Claude Code skills

- Skills:
- - clear-and-concise-humanization: Strunk + Wikipedia AI detection + ten-pass editing
- - explain-code: Visual diagrams and analogies for code explanation
- - extract-book: PDF book to structured Markdown with chapter detection
- - extract-study: Research paper PDF to IMRaD Markdown with DOI/PMID extraction
- - extract-transcript: YouTube/podcast transcript to structured Markdown summary

