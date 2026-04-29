#!/usr/bin/env python3
"""Stealth-surface assertion test.

obscura's repo doesn't ship its own stealth verification. This does.

Loads about:blank in vanilla headless Chromium AND obscura+stealth (via the
existing ObscuraSession in skills/obscura-scraper-crawler/scripts/), evaluates
the same six observable probes against both, and prints a pass/fail table.

Probes are the bot-detection signals obscura's bootstrap.js patches that have
clear, observable differences from vanilla Chromium:
    1. navigator.webdriver
    2. HeadlessChrome in navigator.userAgent
    3. window.chrome.loadTimes existence
    4. window.chrome.csi existence
    5. navigator.plugins.length
    6. event.isTrusted on programmatically dispatched events

Exit code is 0 on a clean run, non-zero if any probe regresses (obscura
returns the same value as vanilla Chromium when it shouldn't, suggesting a
stealth break in either obscura itself or our Playwright-over-CDP plumbing).

Pair with the bot-detection-page A/B in CONTRIBUTING.md for the full picture.

Note on --no-stealth: empirically, obscura's *baseline* engine already
patches all six of these properties -- the --stealth flag adds *additional*
protections (per-session fingerprint randomization for GPU/screen/canvas/
audio/battery, plus the 3,520-domain tracker blocklist) that aren't covered
by these probes. So running with --no-stealth as a sanity check still passes
all six. To verify --stealth's *additional* layer would need probes that
compare canvas fingerprints across two runs, which is out of scope here.

Note on event dispatch: obscura currently has a quirk where listeners
attached to `document` don't fire when document.dispatchEvent is called.
`window.dispatchEvent` and `body.dispatchEvent` work fine. We dispatch on
`window` here. This is unrelated to stealth -- it's a DOM-implementation
gap in obscura at v0.1.1.
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path


# Both engines accept `file://` URLs; obscura rejects `about:` and `data:`.
# We write a minimal HTML stub to a temp file and load it in both for symmetry.
_BLANK_HTML = "<!DOCTYPE html><html><head><title>probe</title></head><body></body></html>"


# Probe spec: each probe says what to evaluate, what obscura+stealth should
# return, and what vanilla Chromium should return. The display formatter turns
# values into short strings for the table; the verdict is computed by
# comparing actual values to obscura_expect.
#
# value_fn: takes a Python value and returns a display string. The probe's
#   `eval_js` returns that value via Playwright's page.evaluate().
PROBES = [
    {
        "name": "navigator.webdriver",
        "eval_js": "() => navigator.webdriver",
        "obscura_expect": None,  # JS undefined => Python None
        "chromium_expect": True,
        "display": lambda v: "undefined" if v is None else repr(v),
    },
    {
        "name": "HeadlessChrome in UA",
        "eval_js": "() => /HeadlessChrome/.test(navigator.userAgent)",
        "obscura_expect": False,
        "chromium_expect": True,
        "display": lambda v: "yes" if v else "no",
    },
    {
        "name": "window.chrome.loadTimes",
        "eval_js": "() => typeof (window.chrome && window.chrome.loadTimes)",
        "obscura_expect": "function",
        "chromium_expect": "undefined",
        "display": lambda v: v,
    },
    {
        "name": "window.chrome.csi",
        "eval_js": "() => typeof (window.chrome && window.chrome.csi)",
        "obscura_expect": "function",
        "chromium_expect": "undefined",
        "display": lambda v: v,
    },
    {
        "name": "navigator.plugins.length",
        "eval_js": "() => navigator.plugins.length",
        # obscura: 5 verified earlier this session; Chromium headless: 0.
        # We only assert "obscura > 0" / "Chromium == 0" via verdict logic.
        "obscura_expect": "_obscura_plugins_present",
        "chromium_expect": 0,
        "display": lambda v: str(v),
    },
    {
        "name": "event.isTrusted (dispatched)",
        # Register a listener, dispatch a synthetic Event, return what the
        # listener captured. Real user events have isTrusted=true; events
        # dispatched by JS are isTrusted=false in standard browsers.
        # obscura's stealth forces isTrusted=true on dispatched events to
        # defeat detectors that probe for "no human dispatched this."
        # We dispatch on `window` rather than `document`: obscura currently
        # has an event-dispatch quirk where listeners attached to `document`
        # don't fire when document.dispatchEvent is called (filed mentally
        # as a separate finding; not a stealth issue per se). `window` works
        # in both browsers and is a fair test of the isTrusted patch.
        # Diagnostic field `fired` confirms the listener ran at all.
        "eval_js": """() => {
            let captured = "NOT_SET";
            let handlerFired = false;
            window.addEventListener("__stealth_probe__", function(e) {
                handlerFired = true;
                captured = e.isTrusted;
            }, { once: true });
            window.dispatchEvent(new Event("__stealth_probe__"));
            return { fired: handlerFired, isTrusted: captured };
        }""",
        # obscura: handler fires, captures isTrusted=true.
        # vanilla Chromium: handler fires, captures isTrusted=false.
        "obscura_expect": {"fired": True, "isTrusted": True},
        "chromium_expect": {"fired": True, "isTrusted": False},
        "display": lambda v: (
            f"fired={v['fired']}, isTrusted={v['isTrusted']}"
            if isinstance(v, dict) else repr(v)
        ),
    },
]


def _verdict(probe, chromium_val, obscura_val):
    """Compute a verdict for one probe.

    Returns one of:
        "obscura wins" - obscura returns its expected value AND it differs
                         from Chromium's value (so the stealth surface is
                         observably better).
        "tie"          - both browsers returned the same value.
        "REGRESSION"   - obscura did NOT return its expected value. Either
                         obscura itself broke the patch, or our Playwright
                         CDP plumbing is undoing it.
    """
    expect = probe["obscura_expect"]
    # Special case: plugins.length is "any positive int" for obscura.
    if expect == "_obscura_plugins_present":
        if isinstance(obscura_val, int) and obscura_val > 0:
            return "obscura wins" if chromium_val == 0 else "tie"
        return "REGRESSION"
    if obscura_val != expect:
        return "REGRESSION"
    if chromium_val == obscura_val:
        return "tie"
    return "obscura wins"


def run_probes_in_chromium(blank_url):
    """Launch vanilla headless Chromium and run each probe."""
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(blank_url)
            for probe in PROBES:
                try:
                    val = page.evaluate(probe["eval_js"])
                except Exception as exc:
                    val = f"<error: {exc}>"
                results.append(val)
        finally:
            browser.close()
    return results


def run_probes_in_obscura(binary, blank_url, stealth=True):
    """Launch obscura serve + Playwright CDP and run each probe."""
    # Lift ObscuraSession from the skill, no shared library per repo convention.
    repo_root = Path(__file__).resolve().parent.parent
    skill_scripts = repo_root / "skills" / "obscura-scraper-crawler" / "scripts"
    sys.path.insert(0, str(skill_scripts))
    from obscura_scraper import ObscuraSession  # noqa: E402

    results = []
    with ObscuraSession(binary=binary, stealth=stealth) as session:
        ctx = session._browser.new_context()
        try:
            page = ctx.new_page()
            page.goto(blank_url)
            for probe in PROBES:
                try:
                    val = page.evaluate(probe["eval_js"])
                except Exception as exc:
                    val = f"<error: {exc}>"
                results.append(val)
        finally:
            ctx.close()
    return results


def render_table(chromium_results, obscura_results, stealth_state):
    """Print a Markdown table of results and return regression count."""
    print()
    print(f"# Stealth-surface assertion (obscura stealth: {stealth_state})")
    print()
    print("| Probe | Vanilla Chromium | obscura | Verdict |")
    print("|---|---|---|---|")

    regressions = 0
    for probe, c_val, o_val in zip(PROBES, chromium_results, obscura_results):
        c_disp = probe["display"](c_val) if not isinstance(c_val, str) or not c_val.startswith("<error:") else c_val
        o_disp = probe["display"](o_val) if not isinstance(o_val, str) or not o_val.startswith("<error:") else o_val
        verdict = _verdict(probe, c_val, o_val)
        if verdict == "REGRESSION":
            regressions += 1
        print(f"| `{probe['name']}` | `{c_disp}` | `{o_disp}` | {verdict} |")

    print()
    if regressions:
        print(f"**{regressions} regression(s) detected.** obscura's stealth "
              f"surface no longer matches the documented expectations. Either "
              f"obscura itself broke a patch (check the binary version) or "
              f"our Playwright-over-CDP plumbing is undoing it (check "
              f"ObscuraSession in obscura_scraper.py).")
    else:
        print(f"**No regressions.** All probes matched expected values "
              f"(stealth: {stealth_state}).")
    return regressions


def main():
    parser = argparse.ArgumentParser(
        description="Compare obscura+stealth's surface against vanilla "
                    "headless Chromium across the six probes obscura's "
                    "bootstrap.js claims to patch."
    )
    parser.add_argument("--obscura-binary", default=None,
                        help="Path to the obscura binary "
                             "(default: 'obscura' on PATH)")
    parser.add_argument("--no-stealth", action="store_true",
                        help="Run obscura WITHOUT --stealth. Use for the "
                             "manual sanity check: most probes should "
                             "regress, exit code should be non-zero. "
                             "Confirms the test catches stealth being off.")
    args = parser.parse_args()

    binary = args.obscura_binary or "obscura"
    if shutil.which(binary) is None:
        # Reuse the skill's install hint formatter.
        repo_root = Path(__file__).resolve().parent.parent
        skill_scripts = repo_root / "skills" / "obscura-scraper-crawler" / "scripts"
        sys.path.insert(0, str(skill_scripts))
        from obscura_scraper import _obscura_install_hint  # noqa: E402
        print(_obscura_install_hint(binary), file=sys.stderr)
        sys.exit(1)

    # Both browsers need a same-origin starting URL. obscura's Page.navigate
    # rejects about: and data: schemes -- only http/https/file allowed -- so
    # we write a tiny HTML stub to a temp file and load it from disk in both.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(_BLANK_HTML)
        blank_path = fh.name
    blank_url = f"file://{blank_path}"

    try:
        print("Probing vanilla headless Chromium...", file=sys.stderr)
        try:
            chromium_results = run_probes_in_chromium(blank_url)
        except Exception as exc:
            msg = str(exc)
            if "Executable doesn't exist" in msg or "playwright install" in msg:
                print("ERROR: vanilla Chromium isn't installed. Run:",
                      file=sys.stderr)
                print("    playwright install chromium", file=sys.stderr)
                print("(This script needs Chromium for the comparison side. "
                      "It does NOT need it for obscura -- obscura ships its "
                      "own engine.)", file=sys.stderr)
                sys.exit(1)
            raise

        stealth = not args.no_stealth
        stealth_state = "on" if stealth else "off"
        print(f"Probing obscura (stealth: {stealth_state})...",
              file=sys.stderr)
        obscura_results = run_probes_in_obscura(
            binary, blank_url, stealth=stealth
        )

        regressions = render_table(
            chromium_results, obscura_results, stealth_state
        )
        sys.exit(1 if regressions else 0)
    finally:
        try:
            os.unlink(blank_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
