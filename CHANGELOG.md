# Changelog

Version `1.0.N` = the Nth commit on `main`. To check out any version:

```bash
git log --oneline main   # find the commit
git checkout <hash>      # check it out
```

## 1.0.19

Add JavaScript rendering to extract-webpage via Playwright

- The static trafilatura fetch returns nothing on React/Vue/Angular SPAs
- because the HTML is just an empty shell before client-side rendering.
- The script now falls back to a headless Chromium browser (via Playwright)
- when the static result is under 50 words, runs trafilatura on the
- fully-rendered HTML, and produces the same Markdown output. Users get
- all pages -- static or JS-rendered -- without flags or extra steps.
- New flags --render and --no-render let callers force or skip the
- browser path.
- Crawl discovery picks up the same fallback. When the sitemap and
- static-HTML link extraction both yield nothing (the SPA shell has no
- <a> tags), discovery renders the start page and harvests links from
- the DOM. aerodrome.finance/docs went from 1 discovered page to 13
- with this change. Discovery also filters out URLs ending in binary
- extensions (.pdf, .zip, image/audio/video formats) before they're
- crawled, because Chromium triggers a download instead of rendering
- for those URLs and was crashing the whole crawl on the first PDF
- link. Per-page errors during a crawl now log and continue rather
- than aborting the entire run.
- Playwright is a soft dependency. The script imports it lazily and
- exits with a clear install command (pip install playwright &&
- playwright install chromium) when a JS page is encountered without
- it. Most users never hit that path. Chromium installs to
- ~/.cache/ms-playwright, shared across all venvs on the machine, so
- it's a one-time per-machine cost rather than per-project.
- SKILL.md, README.md, and the marketplace entry are updated to
- document the new dependency, the auto-fallback behavior, and the
- new flags.

## 1.0.18

Add CONTRIBUTING guide and formalize references/ convention

- Add CONTRIBUTING.md covering setup (including the one-time
- git hooks activation), local testing, the version/changelog
- pipeline, commit-message conventions, and how to add a new
- skill. Link it from README.
- In CLAUDE.md, document two conventions that were implicit:
- the references/ subfolder pattern for offloading domain
- knowledge (already used by clear-and-concise-humanization)
- and the lowercase kebab-case filename contract across the
- extract-* skills.

## 1.0.17

Add Related skills section pointing to vibe-security

- Add a Related skills section to README pointing at Chris Raroque's
- vibe-security skill, which audits AI-generated code for common
- security vulnerabilities. Complementary to this repo's extraction
- and prose skills and installs through the same Skills CLI, so
- pointing users at it costs nothing and expands what they can do
- in one install pass.

## 1.0.16

Standardize extract-* filenames on lowercase kebab-case

- Align the filename guidance across all four extraction skills
- (extract-transcript, extract-study, extract-book, extract-webpage)
- on the same pattern: lowercase kebab-case, identifier-first,
- short slug, full original title preserved in the file's H1.
- Identifier is whatever names the creator for the content type —
- speaker for transcripts, firstauthor+year for studies, author
- for books, author-or-site for webpages. Each SKILL.md now
- spells out the normalization rules (ASCII, lowercase, drop
- middle initials, strip apostrophes/accents) and gives a
- worked example.
- Keeps the marketplace's extraction skills visually and
- behaviorally consistent, avoids URL-encoded spaces in
- cross-references between files, and makes the output
- terminal-friendly without quoting.

## 1.0.15

Enrich extract-transcript with full video metadata and better defaults

- Rewrite get_transcript.py to emit a JSON bundle containing description,
- duration, upload date, chapters, and a timestamped transcript alongside
- the plain-text transcript. Prefer yt-dlp when installed; fall back to
- oembed plus YouTube watch-page scraping so the skill works out of the box.
- Keep --plain flag for the legacy text-only output.
- Update SKILL.md to use the richer bundle: chapter titles become section
- scaffolding, timestamped segments become quote anchors back into the
- video, and description is treated as the primary source for disambiguating
- product names and resource links. Add a first-class "Transcription
- uncertainties" block for proper nouns Claude can't verify, split the
- Step 3 template into argument and tutorial modes, add Published/Runtime
- metadata fields, and default output filing to the session's starting
- directory (with a guard that asks before dumping notes into a code repo).

## 1.0.14

Broaden README to reflect cross-agent install via skills CLI

- These skills follow the Agent Skills standard, so they install into
- Cursor, Gemini CLI, Goose, OpenCode, Windsurf, and others — not only
- Claude Code. Lead with the npx skills install path now that it's the
- broadest entry point.

## 1.0.13

Document distribution channels and release strategy in CLAUDE.md

- - Cover the three working install paths (plugin marketplace, npx skills, symlink)
- - Note the Anthropic plugin directory requires per-plugin restructuring; defer
- - Note mcpmarket likely auto-crawls; let it index organically
- - Releases only at milestones, not every commit

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

