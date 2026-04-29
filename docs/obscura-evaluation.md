# Evaluation: obscura-scraper-crawler vs extract-webpage

> **Status:** evaluation complete, no skill removed. Both ship.
> **Date:** 2026-04-28

## What we evaluated

`obscura-scraper-crawler` is a sister skill to `extract-webpage` introduced in this session. Same Markdown output format, same crawl logic — but every fetch goes through the [obscura](https://github.com/h4ckf0r0day/obscura) headless-browser binary (Rust + V8, custom DOM, ~7.6k stars, v0.1.1) running as a CDP server, with Playwright connecting over `connect_over_cdp(...)`. Stealth on by default.

The question: does obscura provide enough real value to justify a second skill with overlapping logic, a hard binary dependency, and a v0.1.1 maturity profile?

## Methodology

Two complementary tests, both committed:

1. **Real-world A/B** — both skills run against seven URLs spanning Wikipedia (control), docs.dune.com (Cloudflare/Mintlify), TradingView (JS-heavy), G2 reviews (active Cloudflare + DataDome), Crunchbase (hard IP/TLS block), bot.sannysoft.com (canonical headless detection), bot.incolumitas.com (active automation detection). Procedure documented in `CONTRIBUTING.md`.

2. **Stealth-surface assertion** — `scripts/stealth_assertion.py` runs vanilla headless Chromium AND obscura+stealth side-by-side against six observable browser-surface probes derived from `bootstrap.js` in obscura's repo. Network-free, deterministic, exits non-zero on regression.

We also surveyed obscura's own repo via `/opensrc` for benchmarks, fixtures, or stealth tests. None exist. The README claims are accurate but unverified by automation in the project itself.

## Findings

### Surface (the assertion test)

obscura concretely beats vanilla Chromium on all six probes:

| Probe | Vanilla Chromium | obscura+stealth |
|---|---|---|
| `navigator.webdriver` | `true` | `undefined` |
| `HeadlessChrome` in UA | yes | no (`Chrome/145.0.0.0`) |
| `window.chrome.loadTimes` | undefined | function |
| `window.chrome.csi` | undefined | function |
| `navigator.plugins.length` | 0 | 5 |
| `event.isTrusted` (dispatched) | false | true |

Surprise: **obscura's baseline engine already patches all six**, regardless of the `--stealth` flag. Stealth adds *further* protections (per-session GPU/screen/canvas/audio/battery randomization plus the 3,520-domain tracker blocklist) but doesn't gate the basic anti-bot tells. The README's framing implies stealth is opt-in for these; in practice they're always on.

### Real-world (the A/B against bot-walled URLs)

Across all seven URLs, the two skills produced identical or near-identical extracted Markdown:

- **Wikipedia, docs.dune.com, TradingView**: byte-identical or near-identical content, both succeed.
- **G2 reviews**: both fail with 0 words. G2 serves Cloudflare + DataDome active behavioral challenges. Stealth does not defeat behavioral analysis.
- **Crunchbase**: both fail with the same 89-word "you have been blocked" page. Hard IP/TLS reputation block. Stealth does not help once the request is identified at the network layer.
- **bot.sannysoft.com**: both produce readable test-result tables; both fail sannysoft's deeper checks (`WebDriver Advanced`, etc.). Sannysoft uses heuristics beyond what obscura's stealth patches.
- **bot.incolumitas.com**: byte-identical 587-word output.

**Zero pages where obscura succeeded and extract-webpage failed.** The surface-level differences are real but didn't translate to extracted-content differences on the URLs tested.

### Side findings (real bugs surfaced by the A/B)

- **`extract-webpage`'s `fetch_via_curl` was missing `--compressed`.** Sites serving `Content-Encoding: br` (brotli) handed back raw compressed bytes that trafilatura and Readability "extracted" as gibberish. Fixed.
- **`trafilatura.fetch_url` doesn't decode brotli even with the `brotli` Python package installed.** It returned 7KB of garbage on sannysoft that cleared the cascade's word-count threshold via Readability. Fixed by adding `_looks_like_html()` validator in `extract_webpage.py` that skips garbage and advances the cascade.
- **obscura at v0.1.1 has an unrelated DOM gap**: listeners attached to `document` don't fire when `document.dispatchEvent` is called. `window` and `body` work fine. Worth knowing if a target page's JS dispatches events on `document`.

## Decision

**Both skills ship.** Neither is removed.

`extract-webpage` remains the default for everyday URL extraction:
- Lower install friction (`pip install`, no third-party binary, no Gatekeeper dance for browser downloads, no v0.1.1 maturity risk).
- Faster on static HTML (trafilatura is 5–15x faster than rendering a static blog post through V8 + DOM).
- Battle-tested across multiple hardening commits (`docs.dune.com`, `docs.anthropic.com`, `aerodrome.finance/docs` all required real fixes).
- The brotli/garbage-detection fixes from this session put it in better shape than before.

`obscura-scraper-crawler` is the advanced path:
- For sites where extract-webpage's Playwright Chromium leaks `navigator.webdriver=true` or `HeadlessChrome` UA and gets walled.
- For users who want session continuity across crawls (cookies persist, fingerprint stays consistent).
- For workloads where a 70MB single binary is preferred over Playwright's ~300MB Chromium download.

The README's framing reflects this: extract-webpage is presented as the default; obscura-scraper-crawler as the option for bot-walled sites.

## Open questions

1. **Will obscura mature?** v0.1.1 is early. The DOM-event-dispatch gap suggests other surface bugs likely exist. Re-evaluate if v0.2 or later ships with a proper test suite.
2. **Will real-world cases materialize?** The seven URLs we tested didn't show stealth-translates-to-content wins. If contributors hit URLs where extract-webpage returns a challenge stub and obscura-scraper-crawler unlocks them, add those URLs to `CONTRIBUTING.md`'s test list. Three or four such cases would shift the balance toward folding obscura into extract-webpage's cascade as `--fetcher obscura` rather than maintaining a separate skill.
3. **Should we add `playwright-stealth` to extract-webpage's Playwright step?** Would close most of the surface gap without a binary dependency. Deferred — would weaken obscura-scraper-crawler's distinct reason for existing, so revisit only if (2) goes the other way.

## Artifacts

- `scripts/stealth_assertion.py` — surface-level regression test
- `CONTRIBUTING.md` "Testing the web-extraction skills against bot-detection pages" — methodology + URL test list + etiquette + the surface assertion subsection
- `skills/extract-webpage/scripts/extract_webpage.py` — patched with `--compressed` curl flag and `_looks_like_html` validator
- `skills/obscura-scraper-crawler/scripts/obscura_scraper.py` — `ObscuraSession` running obscura serve + Playwright CDP

Re-run the assertion after upgrading obscura, Playwright, or either skill's scripts to catch silent regressions:

```bash
source .venv/bin/activate
python scripts/stealth_assertion.py --obscura-binary /usr/local/bin/obscura
```
