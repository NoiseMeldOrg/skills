# Changelog

Version `1.0.N` = the Nth commit on `main`. To check out any version:

```bash
git log --oneline main   # find the commit
git checkout <hash>      # check it out
```

## 1.0.32

extract-book: drop duplicate TOC chapters, skip venv when pdfplumber exists; humanization: zero em dashes

- - extract_book_pdf.py drops out-of-order duplicate chapter numbers from
- TOC pages that start with a chapter line.
- - SKILL.md: check system pdfplumber before making a venv, read the cover
- page for metadata, how to find ISBNs for KDP books.
- - clear-and-concise-humanization: zero em dashes in anything outgoing.

## 1.0.31

Document extract-transcript bundle JSON schema in SKILL.md

- SKILL.md: added a typed JSON sketch of what scripts/get_transcript.py actually produces, immediately after the existing flat field list. The old list named the keys but not the shapes, so consumers had to read the producer script (or guess) to know whether chapters[i] exposed `start_time` or `start_seconds`, whether transcript_timestamped[i] exposed `t` or `start`, and so on. The new block shows the concrete schema — title/channel/channel_url as strings, description nullable, duration_seconds as int, upload_date as YYYY-MM-DD nullable string, chapters as a nullable list of {title, start_seconds} objects, transcript_plain as a string, transcript_timestamped as a list of {text, start, duration} objects with float seconds, and metadata_source as "yt-dlp" or "fallback".
- SKILL.md: explicit gotcha block follows the schema, calling out the four fields easiest to assume wrong. Chapters use `start_seconds` (a float), not `start_time` / `start` / `timestamp`. There is no `end_time` — chapter-end must be computed from the next chapter's `start_seconds`, or from `duration_seconds` for the last chapter. Timestamped transcript entries use `start` + `duration` (not `t` / `length`); add them for the end of a segment. `chapters` is `null` (not `[]`) when the video has no chapter markers, so consumers must test with `bundle.get("chapters") or []` before iterating, or they'll trip a TypeError. `upload_date` is a normalized YYYY-MM-DD string when metadata_source == "yt-dlp" and may be null on the fallback path.
- No code changes — scripts/get_transcript.py was already emitting these field names; SKILL.md prose just didn't tell consumers what they were. Surfaced when a view script (built off the SKILL's field list) assumed `start_time` and silently produced `0s -> 0s` chapter timestamps across five Ryan Frizelle bundles, only caught during markdown post-processing.
- Verified: re-loaded /tmp/ryan-bundle-1.json (video vSWJipDxcHY, 8 chapters) and confirmed `chapters[0]` is exactly `{"title": "Marrow Dashboard Tour", "start_seconds": 0.0}` — matches the schema block as written.

## 1.0.30

Make extract-webpage portable across project contexts (skill-local venv + user-site install paths)

- SKILL.md: rewrote Setup section to give two clearly labeled install paths instead of assuming a project-local .venv/ at the cwd. Path A is a skill-local venv at {SKILL_DIR}/.venv/ — portable across invocation directories; one-line setup that installs trafilatura + playwright + readability-lxml + markdownify and runs `playwright install chromium`. Path B is `pip3 install --user --break-system-packages …` for users who don't want a per-skill venv; notes PEP 668 and explains that `--break-system-packages` is safe in user-site context because it only writes to ~/Library/Python/3.x/site-packages, never to the system Python. Closing note documents the one-line substitution (`{SKILL_DIR}/.venv/bin/python` for `python3`) if Path A was chosen.
- SKILL.md: replaced `source .venv/bin/activate && python {SKILL_DIR}/scripts/extract_webpage.py` with `python3 {SKILL_DIR}/scripts/extract_webpage.py` in all three invocation examples (Step 1 dry-run, Step 2 single page, Step 2 --crawl). The skill is invoked from arbitrary working directories — often outside any Python project — and the old `source` line silently failed those callers with a "no such file" on .venv/bin/activate, with no signal that the SKILL.md's setup assumption was the problem.
- SKILL.md: added a sentence to the Step 3 Post-Process Title check covering big-typography landing pages where each headline word lives in its own styled <span> (e.g. "The / Claude / Code / Course" stacked vertically). Trafilatura preserves the line breaks and the H1 lands fragmented across multiple lines — tells the agent to merge them into a single H1 in post.
- No code changes — scripts/extract_webpage.py was always callable from python3 once the deps were installed; only the SKILL.md's `source .venv/bin/activate` assumption was wrong.
- Verified: ran the full skill on ryanfrizelle.com from /Volumes/Dock SSD/Source/Repos/NoiseMeldOrg/rapture-mac (no .venv/ at cwd) using Path B; got 951 words of clean content extracted to ~/Documents/notes/webpages/ryan-frizelle-homepage.md, then fixed the fragmented "The / Claude / Code / Course" headline per the new post-process guidance.

## 1.0.29

Add post-commit hook to fold CHANGELOG entries into their own commit

- The commit-msg hook regenerates CHANGELOG.md from git log plus the pending commit message, but it runs AFTER git builds the commit object from the index. So any CHANGELOG changes commit-msg stages land in the NEXT commit, not the current one. This is the one-commit lag that produced orphaned CHANGELOG entries (e.g., v1.0.25 was missing from its own commit, and so was v1.0.27 until the dedicated backfill in v1.0.28).
- The new .githooks/post-commit fixes this. After every commit, the hook checks whether CHANGELOG.md differs from HEAD (which means commit-msg staged a regeneration that didn't land in this commit). If so, it stages CHANGELOG.md and runs git commit --amend --no-edit --no-verify to fold the entry into the just-made commit.
- Loop prevention: --no-verify skips pre-commit and commit-msg, so no CHANGELOG regeneration loop. post-commit DOES run again after the amend (post-commit always runs on amend), but the diff check returns clean the second time (HEAD now matches working tree), and the hook exits.
- Caveat: each commit's hash changes between the initial commit and the post-commit amend. Any external system listening for commit creation events (CI, webhooks) might briefly see a hash that doesn't exist after the amend. For this repo's solo-developer workflow, that's irrelevant.
- CONTRIBUTING.md updated to document the new hook in the Versioning and CHANGELOG section.
- This commit demonstrates the fix: the v1.0.29 entry the commit-msg hook generates for this commit will be folded into this commit by the new post-commit hook, rather than staged for v1.0.30.

## 1.0.28

Backfill 1.0.27 CHANGELOG entry

- The commit-msg hook generates each commit's CHANGELOG entry after the commit is built, which means the entry gets staged for the following commit instead of landing in its own. b59612f shipped to GitHub without its v1.0.27 entry for this reason. This commit lands that entry.
- The same lag carries forward — this commit's v1.0.28 entry will stage for the next one. That's the hook's design, not a bug to fix here.

## 1.0.27

Add accountability-panel skill

- New skill skills/accountability-panel/: a structured-critique skill that runs ideas past a panel of named personas to push back on decisions, plans, and validation-seeking rather than rescue them. Adapted from Craig Doe AI's Accountability Panel concept (https://youtube.com/@craigdoesai); his original was a Google Doc, not a published skill, so this is a clean implementation.
- Five behavioral rules define what separates this skill from generic LLM feedback loops: no rescue (refuse to find angles that make a weak idea work), verdict first (the opener stakes a clear position before the discussion), name the behavior (call out avoidance, shiny-object syndrome, validation-seeking, and sunk-cost ratification when in play), accountability turn (at least once per exchange, a persona turns the question back on the user), and hard recommendation (end with a single directive, not a menu).
- Ships with four working defaults (Partner, Advisor, Colleague, Friend) so the skill is useful out of the box. The skill is meaningfully better when the user replaces those with three to five real people whose judgment they trust — personas.md next to SKILL.md is where customization happens, including an optional Backstory field that preserves the raw context of who each person is.
- Triggers: "Panel" or "Team" call all defined personas; any persona name or user-defined subgroup keyword calls a subset; the skill auto-triggers when the user is clearly seeking validation on a decision ("should I…," "thinking about…," "is this a good idea…," "I'm leaning toward…") and an honest gut-check would serve them better than encouragement.
- Privacy note in personas.md: once the user customizes the file with real people from their life, it becomes journal-grade personal content. The file ships with explicit guidance to keep customized versions in a private repo or local-only — not in a public fork of this repo.
- No Python dependencies. Pure markdown — SKILL.md and personas.md, no scripts directory.
- Added .claude-plugin/marketplace.json entry, alphabetized first in the plugins list. Deliberately NOT added to the extraction-skills bundle (different domain).
- Updated README.md: top-line description expanded from "extracting documents and editing prose" to "extracting documents, editing prose, and structured critique"; install commands list extended with accountability-panel; manual-install symlink list extended with a callout about the customization workflow; new per-skill section added at the end of the Skills section.

## 1.0.26

Harden extract-study against NIHMS/PMC author manuscripts and reversed-cell PDFs

- extract_study_pdf.py: clean_text now filters NIHMS chrome — "HHS Public Access", "Author manuscript", sidebar Author/Manuscript fragments, "<author> et al. Page N" footers, the "...available in PMC..." cite, and "Published in final edited form as".
- extract_study_pdf.py: title detection now skips that same cover matter, glues up to 5 wrapped title lines, joins hyphenated line breaks (cross- + sectional → cross-sectional), and stops at author lines containing a degree token.
- extract_study_pdf.py: new reversed-cell heuristic emits a WARNING at extraction time when 10+ right-to-left cells are detected, telling the user to retry with --layout or fall back to a PMC HTML cross-check.
- extract_study_pdf.py: added five SECTION_ALIASES — Acknowledgments, Funding, Conflicts of Interest, Data Availability, and the BMJ-style "What is Known" / "What This Study Adds" sidebars.
- SKILL.md: setup snippet no longer suppresses pip errors with 2>/dev/null. Checks for pdfplumber import before installing so missing toolchains fail loud rather than as a confusing ModuleNotFoundError.
- SKILL.md: Step 1 now documents what the reversed-cell warning means and what to do.
- SKILL.md: new troubleshooting entries for "Reversed table cells" and "NIHMS / PMC author manuscripts" — the latter promotes PMC HTML cross-check from "consider pulling references" to a default step for nihms-*.pdf files.
- SKILL.md: section-detection list updated to match the new aliases.
- Verified via dry run on a NIHMS PDF: correct title detected, 12 sections found (was 6), reversed-cell warning fires when applicable. Changes live via the existing symlink install. Reference cross-check: Colgan 2022 (PMC8977103 / PMID 34651401).

## 1.0.25

Polish 1.0.24 changelog entry

- Strip the duplicated leading dashes from the auto-generated bullets so the changelog renders cleanly on GitHub. Content unchanged.

## 1.0.24

Add obscura-scraper-crawler skill plus extract-webpage compressed-response fixes

- New skill obscura-scraper-crawler: sister to extract-webpage that runs obscura serve once and connects via Playwright's chromium.connect_over_cdp. Same Markdown output format as extract-webpage so outputs are diffable, stealth on by default, single-page and crawl modes both supported. ObscuraSession context manager handles the obscura process lifecycle and CDP connection.
- Add scripts/stealth_assertion.py: deterministic regression test that runs vanilla headless Chromium and obscura+stealth side by side against six observable browser-surface probes (navigator.webdriver, HeadlessChrome UA, chrome.loadTimes, chrome.csi, plugins.length, event.isTrusted on dispatched events). Prints a Markdown pass/fail table, exits non-zero on regression.
- Add docs/obscura-evaluation.md: strategic decision record covering the A/B methodology, the seven real-world URLs tested, the finding of zero pages where obscura succeeded and extract-webpage failed, the finding that obscura concretely beats vanilla Chromium on all six surface probes, and the decision to keep both skills.
- Fix brotli/gzip handling in extract-webpage's fetch_via_curl by adding --compressed. Without it, sites serving Content-Encoding: br (sannysoft, many CDN-fronted pages) handed back raw compressed bytes.
- Add _looks_like_html validator to extract-webpage's cascade. trafilatura.fetch_url returns brotli garbage that was clearing the cascade's word-count threshold via Readability, so curl and Playwright steps never ran. The validator detects non-HTML bytes and forces advance.
- Update CONTRIBUTING.md with the bot-detection-page testing procedure (URL list, A/B commands, expected outcomes, etiquette) and the stealth-surface assertion subsection.
- Update README.md with the new skill section, install lines, and Python-deps note. Playwright is required for obscura-scraper-crawler but `playwright install` is NOT — CDP connections don't need a Chromium download.
- Add obscura-scraper-crawler entry to .claude-plugin/marketplace.json. Deliberately NOT added to the extraction-skills bundle: the bundle implies everything works after pip install, and obscura's binary dep would silently break that promise.

## 1.0.23

Preserve hand-edited entries in CHANGELOG.md

- Previously the commit-msg hook regenerated the entire changelog from git log on every commit, which silently clobbered any entry that had been polished after the fact (e.g. the curated 1.0.22 release entry got reverted to its raw commit-body form on the next commit). The hook now only writes entries that do not already exist in CHANGELOG.md: the pending commit's entry, plus any historical version missing from the file. Existing entries are preserved verbatim.
- To re-derive an entry from git log (e.g. after a rebase reworded a past commit), delete that version's section from CHANGELOG.md and the next commit will regenerate it.
- Updates CLAUDE.md to reflect the new behavior.

## 1.0.22

Fix two dry-run flag-handling issues in extract-webpage

- Honor --render in --dry-run mode. Previously dry_run() unconditionally forced render="never" for the auto fetcher to keep previews fast, which silently ignored an explicit --render. Now --render and --no-render are preserved when set; the fast-path skip only applies when render is at its default of "auto".
- Suppress the "extraction will continue into Playwright" advisory when Playwright won't actually run during real extraction. The message now fires only when Playwright would be invoked (--fetcher playwright, or auto without --no-render); previously it appeared even with --no-render or --fetcher curl/requests, contradicting the user's flags.
- No behavior change for default invocations, --crawl, or any non-dry-run extraction path.

## 1.0.21

Harden extract-webpage against Cloudflare and JS-rendered docs sites

- Add curl-based fetcher (fetch_via_curl) that bypasses the TLS-fingerprint block Cloudflare applies to the Python requests library. Mintlify, GitBook, Docusaurus v3, and Nextra sites now extract via static fetch instead of falling through to Playwright.
- Change Playwright default wait condition from networkidle to domcontentloaded with a brief content-selector poll. Mintlify-style SPAs keep long-lived analytics websockets open so networkidle never fires and Playwright timed out at 30s with no content; domcontentloaded sidesteps that. networkidle is kept as a last-resort step in the cascade.
- Reorder fetch_and_extract as a cascade: trafilatura.fetch_url -> curl -> Playwright(domcontentloaded) -> Playwright(networkidle). Returns the first result clearing the 50-word threshold; falls back to the best sub-threshold result. Most pages succeed at step 1 or 2 so Playwright is invoked only for genuine SPAs.
- Add --fetcher {auto,requests,curl,playwright} to force a specific fetcher and --wait-until {domcontentloaded,load,networkidle} to override the Playwright wait condition.
- Add a curl-based sitemap fallback to discover_pages. trafilatura.sitemaps.sitemap_search uses requests internally and is blocked by Cloudflare; the fallback fetches /sitemap.xml (and common variants) via curl and expands sitemap-indexes one level. docs.dune.com discovery now finds 1425 URLs that trafilatura returned 0 for.
- Make crawl link discovery cascade through curl too, so JS-only fallback to Playwright doesn't fire when curl can supply the start page's links.
- Update dry_run to walk the static portion of the cascade and report which fetcher succeeded.
- Update SKILL.md to document the cascade, the new flags, and to soften the Cloudflare and JS-rendered limitations now that the cascade handles most cases.
- Verified end-to-end against docs.dune.com (Mintlify+Cloudflare; 183 URLs discovered post-exclude, sample crawl extracts cleanly without Playwright), docs.anthropic.com (curl path), and en.wikipedia.org/wiki/Bitcoin (no regression on plain HTML).

## 1.0.20

Add Readability fallback and path-scoped crawl to extract-webpage

- Fall back to Mozilla's Readability (via readability-lxml + markdownify) when trafilatura returns content but strips all the page's headings -- a failure mode common to SPAs whose content sits in generic divs without semantic markup. The fallback fires only when trafilatura returns zero headings AND Readability returns at least three, AND Readability's word count is within 20% of trafilatura's, so it doesn't trigger on normal articles.
- Default --crawl to path-scoped discovery: when starting at /docs, only follow links whose path starts with /docs. Cuts dApp-style sites that share a domain between docs and an app UI from dozens of discovered URLs to just the relevant ones. Pass --no-scope to disable when peer sections (e.g. /security as a sibling of /docs) hold related docs.
- Document both fallbacks in SKILL.md and update install instructions to include readability-lxml + markdownify.

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

- Cover the three working install paths (plugin marketplace, npx skills, symlink)
- Note the Anthropic plugin directory requires per-plugin restructuring; defer
- Note mcpmarket likely auto-crawls; let it index organically
- Releases only at milestones, not every commit

## 1.0.12

Prepare skills for public release

- Strip personal medical case from extract-transcript SKILL; relevance
- section is now opt-in via project CLAUDE.md
- Genericize archive/docs filing paths in all four extract skills
- Drop --render-images claim from extract-study (script never implemented)
- Soften extract-study metadata claim: authors and journal are manual
- Fix extract-webpage TOC anchors with a GitHub-compatible slugify
- Add CLAUDE.md describing the marketplace, automation, and hook setup

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
- Three install methods (plugin marketplace, global symlink, project-level)
- Python dependency setup
- Per-skill documentation with invoke patterns, options, and examples
- Update instructions for both install methods

## 1.0.3

Allow individual skill installation alongside bundles

- Each skill is now its own installable plugin in the marketplace.
- Bundles (writing-skills, extraction-skills) still available for
- installing groups at once.

## 1.0.2

Add plugin marketplace support and restructure to official pattern

- Restructured to match anthropics/skills convention:
- Skills moved under skills/ directory
- Added .claude-plugin/marketplace.json for plugin install support
- Two plugin groups: writing-skills and extraction-skills
- Updated README with plugin marketplace install instructions
- Added MIT license
- Users can now install via:
- /plugin marketplace add NoiseMeldOrg/skills
- /plugin install writing-skills@noisemeld-skills

## 1.0.1

Initial commit: five custom Claude Code skills

- Skills:
- clear-and-concise-humanization: Strunk + Wikipedia AI detection + ten-pass editing
- explain-code: Visual diagrams and analogies for code explanation
- extract-book: PDF book to structured Markdown with chapter detection
- extract-study: Research paper PDF to IMRaD Markdown with DOI/PMID extraction
- extract-transcript: YouTube/podcast transcript to structured Markdown summary

