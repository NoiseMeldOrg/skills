#!/usr/bin/env python3
"""Take the same screenshots of an app every time, and build the compare page.

Part of the ui-design-cycle skill. One JSON config lists the variants (a base
URL plus a screen size, for example "brand A at phone width") and the screens
(a path plus what to wait for). The script signs in once per variant, visits
every screen, and saves screenshots/<variant>/<screen>-<label>.png. With
--manifest it writes the screen list into compare.html so the review page shows
every before and after pair.

Run with uv so Playwright comes along:

    uv run --with playwright python shoot_screens.py review/shots.json --label before
    uv run --with playwright python shoot_screens.py review/shots.json --label after
    uv run --with playwright python shoot_screens.py review/shots.json --manifest review/compare.html

First time on a machine: uv run --with playwright playwright install chromium

Values written as "env:NAME" are read from the environment and never printed.
Base URLs must be local (localhost, 127.0.0.1, [::1]) unless --allow-remote is
given, so a review run cannot hit a live site by mistake.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "compare.html"


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def resolve(value):
    """Turn "env:NAME" into the environment value; leave anything else alone."""
    if isinstance(value, str) and value.startswith("env:"):
        name = value[4:]
        if name not in os.environ:
            fail(f"environment variable {name} is not set")
        return os.environ[name]
    return value


def load_config(path):
    try:
        cfg = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read config {path}: {e}")
    for key in ("variants", "screens"):
        if not isinstance(cfg.get(key), list) or not cfg[key]:
            fail(f"config needs a non-empty '{key}' list")
    ids = [v["id"] for v in cfg["variants"]]
    if len(ids) != len(set(ids)):
        fail("variant ids must be unique")
    sids = [s["id"] for s in cfg["screens"]]
    if len(sids) != len(set(sids)):
        fail("screen ids must be unique")
    return cfg


def out_dir(cfg, config_path):
    base = Path(config_path).resolve().parent
    return (base / cfg.get("outDir", "screenshots")).resolve()


def screen_variants(screen, cfg):
    wanted = screen.get("variants")
    return [v for v in cfg["variants"] if not wanted or v["id"] in wanted]


def shot_path(root, variant_id, screen_id, label):
    return root / variant_id / f"{screen_id}-{label}.png"


def check_local(cfg, allow_remote):
    for v in cfg["variants"]:
        host = urlparse(v["baseUrl"]).hostname or ""
        if host not in LOCAL_HOSTS and not allow_remote:
            fail(f"variant {v['id']} points at {host}, not a local address. "
                 "Use --allow-remote only for a deliberate check of a live site.")


def build_url(variant, path):
    url = variant["baseUrl"].rstrip("/") + "/" + path.lstrip("/")
    query = variant.get("query", "")
    if query:
        url += ("&" if "?" in url else "?") + query.lstrip("?&")
    return url


def run_actions(page, actions, variant):
    for a in actions or []:
        if "goto" in a:
            page.goto(build_url(variant, a["goto"]), wait_until="networkidle")
        elif "fill" in a:
            page.fill(a["fill"], resolve(a.get("value", "")))
        elif "click" in a:
            page.click(a["click"])
        elif "press" in a:
            page.press(a.get("selector", "body"), a["press"])
        elif "waitFor" in a:
            page.wait_for_selector(a["waitFor"], timeout=a.get("timeout", 15000))
        elif "waitForUrl" in a:
            page.wait_for_url(re.compile(a["waitForUrl"]), timeout=a.get("timeout", 15000))
        elif "wait" in a:
            page.wait_for_timeout(int(a["wait"]))
        else:
            fail(f"unknown action {a}")


def shoot(cfg, config_path, label, only, only_variants, dry_run):
    root = out_dir(cfg, config_path)
    plan = []
    for v in cfg["variants"]:
        if only_variants and v["id"] not in only_variants:
            continue
        for s in cfg["screens"]:
            if only and s["id"] not in only:
                continue
            if v not in screen_variants(s, cfg):
                continue
            plan.append((v, s, shot_path(root, v["id"], s["id"], label)))
    if not plan:
        fail("nothing to shoot with these filters")
    if dry_run:
        for v, s, p in plan:
            print(f"{v['id']:<16} {s['id']:<24} {build_url(v, s['path'])} -> {p}")
        print(f"{len(plan)} screenshot(s) planned, label '{label}'. Nothing taken (dry run).")
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail("Playwright is missing. Run with: uv run --with playwright python shoot_screens.py ...")

    logins = cfg.get("logins", {})
    failures = []
    taken = 0
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as e:  # noqa: BLE001
            if "Executable doesn't exist" in str(e):
                fail("Playwright's browser is not installed. Run once: uv run --with playwright playwright install chromium")
            raise
        by_variant = {}
        for v, s, p in plan:
            by_variant.setdefault(v["id"], (v, []))[1].append((s, p))
        for vid, (v, items) in by_variant.items():
            def new_context():
                return browser.new_context(
                    viewport={"width": int(v.get("width", 390)), "height": int(v.get("height", 844))},
                    device_scale_factor=float(v.get("scale", 2)),
                    is_mobile=bool(v.get("mobile", int(v.get("width", 390)) < 600)),
                    has_touch=bool(v.get("touch", int(v.get("width", 390)) < 1024)),
                )
            # Signed-out screens (sign-in, password reset) get a fresh context with no session.
            signed_out = [(s, p) for s, p in items if s.get("signedOut")]
            signed_in = [(s, p) for s, p in items if not s.get("signedOut")]
            for group, needs_login in ((signed_out, False), (signed_in, True)):
                if not group:
                    continue
                context = new_context()
                page = context.new_page()
                login = v.get("login") if needs_login else None
                if login:
                    if login not in logins:
                        fail(f"variant {vid} names login '{login}', which the config does not define")
                    try:
                        run_actions(page, logins[login], v)
                    except Exception as e:  # noqa: BLE001 - report and keep going
                        failures.append(f"{vid}: sign-in failed: {str(e).splitlines()[0]}")
                        context.close()
                        continue
                for s, p in group:
                    try:
                        page.goto(build_url(v, s["path"]), wait_until="networkidle")
                        run_actions(page, s.get("actions"), v)
                        if s.get("waitFor"):
                            page.wait_for_selector(s["waitFor"], timeout=15000)
                        page.wait_for_timeout(int(s.get("settle", 300)))
                        p.parent.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(p), full_page=bool(s.get("fullPage", True)))
                        taken += 1
                        print(f"ok   {vid:<16} {s['id']}")
                    except Exception as e:  # noqa: BLE001
                        failures.append(f"{vid} / {s['id']}: {str(e).splitlines()[0]}")
                        print(f"FAIL {vid:<16} {s['id']}")
                context.close()
        browser.close()
    print(f"\n{taken} screenshot(s) saved to {root} with label '{label}'.")
    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    return 0


def write_manifest(cfg, config_path, compare_path):
    compare = Path(compare_path).resolve()
    if not compare.exists():
        if not TEMPLATE.exists():
            fail(f"template not found at {TEMPLATE}")
        compare.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TEMPLATE, compare)
        print(f"copied the template to {compare}")
    root = out_dir(cfg, config_path)
    screens, missing = [], []
    for s in cfg["screens"]:
        shots = {}
        for v in screen_variants(s, cfg):
            pair = {}
            for label in ("before", "after"):
                p = shot_path(root, v["id"], s["id"], label)
                if p.exists():
                    pair[label] = os.path.relpath(p, compare.parent)
                else:
                    missing.append(os.path.relpath(p, compare.parent))
            if pair:
                shots[v["id"]] = pair
        if shots:
            screens.append({
                "id": s["id"],
                "group": s.get("group", ""),
                "name": s.get("name", s["id"]),
                "changed": s.get("changed", []),
                "shots": shots,
            })
    manifest = {
        "title": cfg.get("title", "Before and after review"),
        "cycle": cfg.get("cycle", ""),
        "notice": cfg.get("notice", ""),
        "variants": [{"id": v["id"], "label": v.get("label", v["id"]), "width": int(v.get("width", 390))} for v in cfg["variants"]],
        "screens": screens,
    }
    html = compare.read_text()
    block = re.compile(r'(<script id="manifest" type="application/json">)(.*?)(</script>)', re.S)
    if not block.search(html):
        fail(f"{compare} has no manifest block; start from the template")
    body = json.dumps(manifest, indent=2, ensure_ascii=False).replace("</", "<\\/")
    html = block.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(3), html, count=1)
    compare.write_text(html)
    print(f"wrote {len(screens)} screen(s) into {compare}")
    if missing:
        print(f"{len(missing)} screenshot(s) missing (shown as 'No image' on the page):")
        for m in missing[:30]:
            print(f"  - {m}")
        if len(missing) > 30:
            print(f"  ... and {len(missing) - 30} more")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Screenshot every screen the same way, and build compare.html.")
    ap.add_argument("config", help="path to the shots JSON config")
    ap.add_argument("--label", help="before or after (any word works; it names the files)")
    ap.add_argument("--only", help="comma-separated screen ids")
    ap.add_argument("--variants", help="comma-separated variant ids")
    ap.add_argument("--manifest", metavar="COMPARE_HTML", help="write the screen list into this compare.html")
    ap.add_argument("--allow-remote", action="store_true", help="allow base URLs that are not local")
    ap.add_argument("--dry-run", action="store_true", help="list what would be shot, take nothing")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.manifest:
        return write_manifest(cfg, args.config, args.manifest)
    if not args.label:
        fail("give --label before or --label after (or --manifest)")
    if not re.fullmatch(r"[a-z0-9-]+", args.label):
        fail("label must be lowercase letters, digits or dashes")
    check_local(cfg, args.allow_remote)
    only = set(args.only.split(",")) if args.only else None
    only_variants = set(args.variants.split(",")) if args.variants else None
    return shoot(cfg, args.config, args.label, only, only_variants, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
