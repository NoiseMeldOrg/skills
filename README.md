# NoiseMeld Skills

Agent skills for extracting documents, editing prose, structured critique, and planning projects that span many agent sessions. Built on the [Agent Skills](https://agentskills.io) open standard, so they install cleanly into Claude Code, Codex, Cursor, Gemini CLI, Goose, OpenCode, Windsurf, and other compatible agents. Each skill is a folder under `skills/` with a `SKILL.md`.

## Installation

`~/.agents/skills` is the standard home for global skills, and most agents read it directly. Claude Code reads `~/.claude/skills` instead; one symlink points it at the standard folder (see [agentcanon](https://github.com/buildermethods/agentcanon)). Every option below except the plugin marketplace installs into the standard folder.

### Option 1: Skills CLI (recommended, updates itself)

```bash
npx skills add https://github.com/NoiseMeldOrg/skills --skill extract-book -g
```

Swap `extract-book` for `extract-study`, `extract-transcript`, `extract-webpage`, `obscura-scraper-crawler`, `clear-and-concise-humanization`, `accountability-panel`, `cycle-orchestration`, or `ui-design-cycle`. `-g` installs globally into `~/.agents/skills` and links it for every agent the CLI finds; leave it off to install into the current project only.

Update later with `npx skills update`. List installed skills with `npx skills list`.

### Option 2: Ask your agent

Paste this into any agent:

```
Install the skills from github.com/NoiseMeldOrg/skills into my global skills folder (~/.agents/skills), and make sure my agent can read that folder.
```

### Option 3: Clone and symlink

Clone once, then link the skills you want into the standard folder:

```bash
git clone https://github.com/NoiseMeldOrg/skills.git ~/skills
mkdir -p ~/.agents/skills

ln -s ~/skills/skills/extract-book ~/.agents/skills/
ln -s ~/skills/skills/extract-study ~/.agents/skills/
ln -s ~/skills/skills/extract-transcript ~/.agents/skills/
ln -s ~/skills/skills/extract-webpage ~/.agents/skills/
ln -s ~/skills/skills/obscura-scraper-crawler ~/.agents/skills/
ln -s ~/skills/skills/clear-and-concise-humanization ~/.agents/skills/
ln -s ~/skills/skills/accountability-panel ~/.agents/skills/
ln -s ~/skills/skills/cycle-orchestration ~/.agents/skills/
ln -s ~/skills/skills/ui-design-cycle ~/.agents/skills/
```

If you use Claude Code and `~/.claude/skills` is not already a symlink to `~/.agents/skills`, link each skill there too (`ln -s ~/skills/skills/extract-book ~/.claude/skills/`), or follow [agentcanon](https://github.com/buildermethods/agentcanon) to make the whole folder one symlink.

Pull the repo to update. Symlinks pick up changes immediately, and skill names stay short (`/extract-book`, no namespace).

**Note for `accountability-panel`:** the skill is meant to be customized. `personas.md` next to `SKILL.md` is where you replace the four shipped defaults with real people whose judgment you trust. If you symlink, edits land in this repo. To keep your customized `personas.md` private, copy the skill into `~/.agents/skills/accountability-panel/` instead of symlinking, and edit it there. See the privacy note at the bottom of `personas.md`.

### Option 4: Claude Code plugin marketplace

Register the marketplace once:

```
/plugin marketplace add NoiseMeldOrg/skills
```

Install the skills you want:

```
/plugin install extract-book@noisemeld-skills
/plugin install extract-study@noisemeld-skills
/plugin install extract-transcript@noisemeld-skills
/plugin install extract-webpage@noisemeld-skills
/plugin install obscura-scraper-crawler@noisemeld-skills
/plugin install clear-and-concise-humanization@noisemeld-skills
/plugin install accountability-panel@noisemeld-skills
/plugin install cycle-orchestration@noisemeld-skills
/plugin install ui-design-cycle@noisemeld-skills
```

Or grab a bundle:

```
/plugin install extraction-skills@noisemeld-skills    # all four extract skills
```

Plugin skills are namespaced (`/noisemeld-skills:extract-book`) and work in Claude Code only.

### Project-level install

Add a skill to one project so your team gets it through version control:

```bash
mkdir -p /path/to/project/.agents/skills
ln -s ~/skills/skills/extract-study /path/to/project/.agents/skills/
```

For Claude Code, also point the project's `.claude/skills` at it: `ln -s ../.agents/skills /path/to/project/.claude/skills` (when the project has no `.claude/skills` folder yet).

### Python dependencies

The extract skills need Python packages:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pdfplumber youtube_transcript_api trafilatura playwright
playwright install chromium
```

`extract-book` and `extract-study` use `pdfplumber`. `extract-transcript` uses `youtube_transcript_api` when fetching from YouTube URLs (pasted transcripts need nothing). `extract-webpage` uses `trafilatura` for static HTML and falls back to `playwright` (with a bundled Chromium) for JavaScript-rendered pages.

`obscura-scraper-crawler` is a separate path for sites behind Cloudflare/bot walls. It needs `trafilatura`, `readability-lxml`, `markdownify`, `lxml`, `playwright`, and the [obscura](https://github.com/h4ckf0r0day/obscura/releases) binary on PATH. It uses Playwright purely as a CDP client to drive `obscura serve`, so you do NOT need `playwright install` -- obscura ships its own browser engine.

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

The script detects standard section headings (Abstract, Methods, Results, Discussion, Conclusion, References) and pulls title, year, DOI, and PMID/PMCID from the first pages. Authors and journal are filled in by hand during the post-process step.

Flags: `--dry-run` to preview, `--layout` for two-column PDFs, `-o path.md` to set the output path.

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

The bundled script uses trafilatura for static HTML and automatically falls back to a headless Chromium (via Playwright) when a page returns sparse content -- so React, Vue, and Angular SPAs work the same way as plain HTML pages. Authenticated pages still won't work; the headless browser uses a fresh profile with no cookies.

Flags: `--dry-run` to preview, `--crawl` for multi-page, `--max-pages N` to limit crawl, `--no-links` to strip hyperlinks, `--exclude /pattern/` to filter URLs, `--no-exclude` to disable default filtering, `--render` to force browser rendering, `--no-render` to disable the JS fallback for speed.

---

### obscura-scraper-crawler

Sister skill to extract-webpage for Cloudflare and bot-walled sites. Routes every fetch through the [obscura](https://github.com/h4ckf0r0day/obscura) headless browser binary with stealth on by default (per-session fingerprint randomization, `navigator.webdriver = undefined`, native-function masking, plus a 3,520-domain tracker blocklist). Same Markdown output format as extract-webpage so the two are directly comparable on the same URL.

Give Claude a URL with "use obscura" or "scrape with stealth," or run `/obscura-scraper-crawler https://example.com/article`. Same dry-run-then-extract-then-post-process flow as extract-webpage. Crawl mode supported via `--crawl`.

Stealth defeats most passive client-side bot checks. It does NOT defeat active interstitials with behavioral analysis (Turnstile, hCaptcha) -- those need a real browser session. For default URL extraction prefer extract-webpage (faster, lighter, no binary dep).

Architecture: the script starts `obscura serve --stealth` once and connects via Playwright's `chromium.connect_over_cdp(...)`. One obscura process backs the whole run, cookies persist across pages, and Playwright provides the navigation API while obscura provides the stealth surface (`navigator.webdriver: undefined`, realistic UA, `window.chrome` present).

Requires the obscura binary on PATH (prebuilt releases at https://github.com/h4ckf0r0day/obscura/releases) plus `trafilatura`, `readability-lxml`, `markdownify`, `lxml`, and `playwright`. You do NOT need to run `playwright install` -- CDP connections don't need a Chromium download.

Flags: `--dry-run`, `--crawl`, `--max-pages N`, `--no-stealth`, `--wait-until {load,domcontentloaded,networkidle0}`, `--obscura-wait N`, `--obscura-selector CSS`, `--obscura-binary PATH`, `--obscura-port N`, `--no-links`, `--include-images`, `--exclude /pat/`, `--no-exclude`, `--no-scope`, `--delay N`, `-o path.md`.

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

### accountability-panel

Runs an idea past a panel of named personas who push back rather than encourage. Refuses to rescue weak ideas — names the pattern that generated them (avoidance, shiny-object syndrome, validation-seeking, sunk-cost ratification) instead of finding angles to make them work.

Trigger with "Panel," "Team," a persona name, or any subgroup keyword defined in `personas.md`. Auto-triggers when the user is clearly seeking validation on a decision ("should I…," "is this a good idea…," "I'm leaning toward…") and an honest gut-check would serve them better than encouragement.

The skill follows five behavioral rules that separate it from generic LLM feedback loops: no rescue (refuse to find angles that make a weak idea work), verdict first (the opener stakes a clear position before the discussion), name the behavior (call out the pattern in play), accountability turn (at least once per exchange, a persona turns the question back on the user), and hard recommendation (end with a single directive, not a menu).

Ships with [Craig Doe AI](https://youtube.com/@craigdoesai)'s four-persona default (Partner, Advisor, Colleague, Friend) so it's useful immediately. The skill is meaningfully better when you replace those with three to five real people whose judgment you trust — edit `personas.md` next to `SKILL.md`. An optional Backstory field preserves the raw context of who each person is to you, which keeps each voice from collapsing back into an archetype.

**Privacy note:** once you customize `personas.md` with real people from your life, that file becomes journal-grade personal content. Keep your customized version in a private repo or local-only — not a public fork of this one. The skill ships with the same privacy note inside `personas.md` so anyone customizing it sees the warning.

No Python dependencies. Pure markdown — `SKILL.md` and `personas.md`.

---

### cycle-orchestration

Runs any job that needs more than one agent session as a dated "cycle": a new feature, a redesign, a strategy session, a piece of content. Plans live in files instead of one chat, so a fresh agent can pick up the work from a single sentence like "review the newest cycle and start phase 2."

Each cycle gets a folder, `cycles/YYYY-MM-DD-short-name/`, with a living `summary.md` that the agents keep current: status, next step, decisions, and what went wrong. Small jobs stop there. Big jobs get a PRD and one folder per phase, each with a brief, a build log, a review by a separate reviewer agent, and screenshots where there is a screen. The agent stops after every phase and waits for your "go." Say "lock it" during planning and the decision is written to a file on the spot.

For big jobs it calls `bm-prd-creator` from [Builder Methods' bm-skills](https://github.com/buildermethods/bm-skills) to write the PRD and phase prompts. Without it, the skill offers to write a lighter plan itself.

Based on the planning method Brian Casel shows in [How I plan (large) projects with agents](https://www.youtube.com/watch?v=krhkmockjCM). His own "cycle orchestration" skill is not public; this is an independent version built from the video.

No Python dependencies. Pure markdown: `SKILL.md`, eight step files, and templates for `summary.md` and the review report.

---

### ui-design-cycle

Runs a UI polish or redesign of an existing app as a cycle, so an agent can restyle many screens to a high standard without you losing control of what ships. It changes how the app looks, never what it does.

It starts with an audit of the real code (fonts, colors, hard-coded values, theme mode, shared brands, every screen) before asking any design question. Then it locks the look one decision at a time: which screens first, font, colors, shape, dark mode, and what is out of scope. Phases follow a standard shape: foundation and first-impression screens, the rest of the user screens plus a review kit, then admin screens to match. Work happens on a branch, and nothing is pushed or deployed until you have reviewed it.

The review kit is the point. `compare.html` shows every screen before and after, side by side or flipped in place, for each brand and screen width, with Approve and Flag buttons and a "Copy review notes" button that hands your flags back to the agent. `run-local.sh` runs the original and new apps side by side on your machine against local databases only, and refuses to start if a database URL points anywhere else. `checklist.md` is the hands-on walkthrough.

You can run the phases attended, one session per phase, or unattended with Claude Code's `/goal` in auto mode; the skill writes the goal text, which stops before any push.

Requires `cycle-orchestration`. Uses `bm-prd-creator` for the PRD and `impeccable` for the design passes when they are installed. Ships `scripts/shoot_screens.py`, which takes every screenshot the same way (every screen, width and brand, signed in or out) from one `shots.json` and fills in the compare page. It needs Playwright; run it with `uv run --with playwright python ...` and install the browser once with `uv run --with playwright playwright install chromium`.

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

## Versioning

Version numbers track the commit count on `main`: version `1.0.N` is the Nth commit. This is automatic -- a pre-commit hook updates `marketplace.json` on every commit. No manual version bumping.

To find the exact code for any version:

```bash
git log --oneline main | head -N
```

For example, version `1.0.9` corresponds to the 9th commit on main.

See [CHANGELOG.md](CHANGELOG.md) for what changed in each version.

---

## Updating

### Plugin marketplace

Claude Code does not notify you when plugins update. Two options:

**Manual check:** Run `/plugin update <skill-name>` to pull the latest version of a specific skill, or update all installed plugins from a marketplace at once.

**Auto-update:** Enable per-marketplace in Claude Code via `/plugin` > Marketplaces tab. When enabled, Claude Code checks for new versions on startup. Third-party marketplaces (like this one) have auto-update off by default -- you opt in.

After updating, restart Claude Code for the new skill definitions to load.

### Symlink install

Pull the repo. Symlinks pick up changes immediately -- no reinstall needed.

```bash
cd ~/skills && git pull
```

Check the current version:

```bash
./scripts/set_version.sh --check
```

### How to tell if an update is available

Watch the repo on GitHub (Settings > Watch > Releases) to get notified of new versions. Or just pull periodically -- the changelog shows what changed.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, local testing, the version/changelog hooks, commit-message conventions, and how to add a new skill.

---

## Related skills

Skills maintained outside this repo that pair well with it:

- **[bm-skills](https://github.com/buildermethods/bm-skills)** by [Brian Casel](https://buildermethods.com) at Builder Methods: PRD Creator, Skill Builder, Design System and Favicon Creator. `cycle-orchestration` uses PRD Creator for big jobs, and Skill Builder is a good way to write new skills in this repo's style.

  ```
  /plugin marketplace add buildermethods/bm-skills
  /plugin install bm-skills
  ```

- **[vibe-security](https://github.com/raroque/vibe-security-skill)** by [Chris Raroque](https://github.com/raroque) and Aloa — audits AI-generated code for common security vulnerabilities: hardcoded secrets, missing row-level security, client-submitted prices, tokens stored in localStorage, and six more categories. Covers secrets, database security, auth, rate limiting, payments, mobile, AI/LLM integration, deployment, and data access, each with before/after examples. MIT licensed. Works with Claude Code and OpenAI Codex.

  ```bash
  npx skills add https://github.com/raroque/vibe-security-skill --skill vibe-security
  ```

The Skills CLI handles both repos identically, so external skills install alongside these without conflict and update together via `npx skills update`.

---

## License

MIT
