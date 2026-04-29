# Contributing

Thanks for wanting to help. This repo is a Claude Code plugin marketplace publishing skills for document extraction and prose editing. Here's what you need to know to contribute effectively.

## Setup

Clone the repo and activate the git hooks (one-time, per clone):

```bash
git clone https://github.com/NoiseMeldOrg/skills.git
cd skills
git config core.hooksPath .githooks
```

The hooks auto-bump the version and regenerate `CHANGELOG.md` on every commit. See [Versioning](#versioning-and-changelog-automatic--dont-fight-the-hooks) below.

## Testing a skill locally

Symlink the skill into your global `~/.claude/skills/` directory:

```bash
ln -s "$(pwd)/skills/extract-book" ~/.claude/skills/
```

Start a new Claude Code session and the skill will load. Edits to `SKILL.md` or scripts take effect on the next skill invocation — no reinstall needed.

For the Python-based extract skills, install the dependencies:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pdfplumber youtube_transcript_api trafilatura
```

Test each script directly against a sample input (`--dry-run` is your friend) before committing. There are no unit tests — the contract is "the script produces reasonable output for real files, and the `SKILL.md` prose tells Claude how to clean up what it misses."

## Testing the web-extraction skills against bot-detection pages

Both `extract-webpage` and `obscura-scraper-crawler` have a class of failure modes that are hard to catch with regular URLs: brotli/gzip decoding bugs, headless-browser tells (`navigator.webdriver`, `HeadlessChrome` UA), and CDN-served challenge pages. Three public test pages exist exactly for this kind of verification — they're designed to be hit by automated tools, so a single request per change is appropriate and within their intended use.

| Site | What it tests | Use it to verify |
|---|---|---|
| `https://bot.sannysoft.com/` | Renders a pass/fail table for ~40 headless-detection signals: `navigator.webdriver`, `window.chrome`, plugin arrays, WebGL vendor, canvas fingerprints, etc. Serves Brotli-encoded HTML by default. | (1) Compressed-response decoding works (output should be readable Markdown, not binary). (2) The renderer Playwright/obscura uses doesn't leak the simplest webdriver tells. (3) New stealth tactics actually flip cells from "failed" to "passed". |
| `https://bot.incolumitas.com/` | Active automation detection (TCP/IP fingerprinting, behavioral checks, runtime API probing). Useful as a second opinion when something passes sannysoft. | (1) Pipeline works end-to-end on a JS-rendered page. (2) Stealth claims hold up against a different detector. |
| `https://www.scrapfly.io/web-scraping-tools/automation-detector` | Scrapfly's own pass/fail check for Selenium/Puppeteer/Playwright signals. Good for spot-checks. | Smoke test only. |

### How to run an A/B locally

```bash
source .venv/bin/activate

# Pick a URL and run both skills, write outputs side-by-side
URL="https://bot.sannysoft.com/"
python skills/extract-webpage/scripts/extract_webpage.py "$URL" -o /tmp/ew.md
python skills/obscura-scraper-crawler/scripts/obscura_scraper.py "$URL" -o /tmp/os.md

# Diff the two
diff /tmp/ew.md /tmp/os.md

# Word counts; identical means parity, divergence means one of them is doing
# something different (better or worse — read both)
wc -w /tmp/ew.md /tmp/os.md
```

`obscura-scraper-crawler` needs the `obscura` binary on `PATH` (or pass `--obscura-binary /path/to/obscura`). See its `SKILL.md` for install instructions.

### Expected outcomes (current baseline as of 1.0.32)

- **sannysoft**: both skills produce a readable test-results table. Both currently fail at least `WebDriver (New)`, `WebDriver Advanced`, and `Chrome (New)` — sannysoft uses checks deeper than the basic `navigator.webdriver` property. Obscura's stealth doesn't change these specific cells; this is *known and expected* until either obscura's stealth gets stronger or we add a different renderer.
- **incolumitas**: both skills produce ~600 words of byte-identical output. The site's verdict (bot/not bot) is in a JS-rendered widget that the static extractors don't capture, so the Markdown comparison is mostly a "does the pipeline work" check, not a stealth comparison.
- **Garbled-binary regression test**: if anyone ever removes `--compressed` from `fetch_via_curl` *or* the `_looks_like_html` check from the cascade, sannysoft's extract-webpage output will revert to non-UTF-8 binary garbage. That's the canary — if the output of `python skills/extract-webpage/scripts/extract_webpage.py "https://bot.sannysoft.com/"` doesn't open cleanly as Markdown, the brotli regression is back.

### When to run these tests

- Anytime you change `fetch_via_curl`, `fetch_rendered`, the cascade order in `_build_fetch_plan`, or `_looks_like_html`.
- Anytime you upgrade `trafilatura`, `playwright`, or the obscura binary.
- When a new site shows up in the wild that one skill handles and the other doesn't — adding a regression test means dropping its URL into the list above with the expected outcome.

### Etiquette

These pages exist for exactly this purpose, so a handful of requests per development cycle is fine. Don't `--crawl` against them, don't loop, and don't include them in any automated CI that runs on every push — periodic manual checks are the right cadence.

For the strategic finding from the 2026-04-28 evaluation (why both skills ship, what we learned about obscura's surface vs real-world behavior), see [`docs/obscura-evaluation.md`](docs/obscura-evaluation.md).

### Stealth-surface assertion (network-free, deterministic)

obscura's repo doesn't ship its own stealth verification, so we ship one. Run after upgrading the obscura binary, the `playwright` Python package, or anything in `skills/obscura-scraper-crawler/scripts/`:

```bash
source .venv/bin/activate
python scripts/stealth_assertion.py --obscura-binary /usr/local/bin/obscura
```

Loads a tiny `file://` HTML stub in vanilla headless Chromium AND obscura+stealth (via the existing `ObscuraSession`), queries six observable properties obscura's `bootstrap.js` patches, prints a Markdown pass/fail table, exits non-zero on regression. No network — this tests the surface obscura claims to expose, not whether any real site cares. Pair with the bot-detection-page A/B above for the full picture.

Current baseline: all six probes report "obscura wins" on a fresh install (`navigator.webdriver: undefined`, no `HeadlessChrome` in UA, `chrome.loadTimes`/`chrome.csi` stubbed in, `plugins.length: 5` vs Chromium's `0`, `event.isTrusted: true` on `window.dispatchEvent`). If a future upgrade flips any cell to "REGRESSION", obscura silently broke a patch or our Playwright-over-CDP plumbing started undoing one.

Findings worth knowing:
- **obscura's baseline engine already patches all six**, regardless of `--stealth`. The `--stealth` flag adds further protections (per-session GPU/screen/canvas/audio/battery randomization plus the 3,520-domain tracker blocklist) that this script doesn't probe — testing those would need cross-run fingerprint comparison.
- **obscura at v0.1.1 has an event-dispatch quirk:** listeners attached to `document` don't fire when `document.dispatchEvent` is called. `window.dispatchEvent` and `body.dispatchEvent` work. Unrelated to stealth, but bites the obvious form of the `isTrusted` probe.

## Versioning and CHANGELOG (automatic — don't fight the hooks)

- Version is `1.0.<commit-count-on-main>`, rewritten into `.claude-plugin/marketplace.json` by the pre-commit hook.
- `CHANGELOG.md` is regenerated from `git log` by the commit-msg hook.
- **Never hand-edit** `metadata.version` or any entry in `CHANGELOG.md` — both get overwritten on the next commit.
- Check the current version without writing: `./scripts/set_version.sh --check`.

## Commit messages

The first line of every commit becomes a changelog heading; body lines become bullets. Write accordingly:

```
Fix column-bleed detection in extract-study

- Detect three-column layouts using column-width variance
- Fall back to two-column when variance is inconclusive
```

Not:

```
fixed a bug
```

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`, optional `when_to_use`, optional `paths`). Front-load the actual trigger phrases a user would type — Claude under-triggers skills with vague descriptions.
2. If the skill ships a script, add `skills/<name>/scripts/<name>.py`. Scripts are standalone (no shared library), depend on at most one PyPI package, and support `--dry-run` where preview behavior is useful.
3. For domain-heavy skills, put bundled knowledge in `skills/<name>/references/<topic>.md` and cite by path from `SKILL.md`. Keeps the SKILL.md prose lean.
4. Add a `plugins[]` entry to `.claude-plugin/marketplace.json` pointing at `./skills/<name>`. If the skill fits the extraction bundle, add it to `extraction-skills.skills` as well.
5. Update `README.md` with the install block and a short skill description.

## Editing an existing skill

- **`SKILL.md` prose** — free to edit, but trigger descriptions are functional: wording affects whether Claude fires the skill. The README's "Making skills trigger reliably" section explains the model.
- **Scripts** — test against a sample input before committing. The extract skills follow a "dry run, then extract, then post-process with Claude's judgment" pattern; move logic into scripts only when it's deterministic enough to not need Claude's review.
- **Filenames produced by the skills** — all four extract skills default to lowercase kebab-case (e.g., `tom-solid-note-taking-apps.md`). Keep new skill output consistent with that convention.

## What not to do

- Don't hand-edit `metadata.version` in `marketplace.json` or `CHANGELOG.md` entries.
- Don't add emoji to skill content or scripts.
- Don't fork third-party skills into this repo — reference them in the README's "Related skills" section so `npx skills update` keeps working for users.
- Don't skip the hooks (`--no-verify`). If a hook fails, fix the underlying issue; the hooks are load-bearing for the versioning and changelog pipeline.

## Proposing changes

Open a pull request against `main`. Small, single-purpose PRs merge fastest. If the change is structural or the direction is uncertain, open an issue first so we can align before you write the code.

## License

By contributing, you agree your work is licensed under this repo's [MIT license](LICENSE).

## Questions

Open an issue at [github.com/NoiseMeldOrg/skills/issues](https://github.com/NoiseMeldOrg/skills/issues).
