# Start and audit

## Start the cycle

Run `cycle-orchestration` steps 1 and 2 (find or start, size). Name the folder for the design job, for example `cycles/YYYY-MM-DD-design-polish/`. A design pass over more than a handful of screens is a **big** cycle: it touches many files, it is visible to every user, and the review needs its own phase. Recommend big unless it is one or two screens.

Write the deadline into the Goal in `summary.md`. If the design work is standing between the user and something harder (calls, a launch, a sale), say so plainly once, offer to do the harder thing first, and let the user choose. If they choose the design work, write the deadline and what happens after it into Decisions, so the deadline holds.

## Audit before deciding

Do this before asking any design question. Read, do not change:

1. **Design docs**: the repo `CLAUDE.md` design section, any `.impeccable.md`, design critiques or audits, brand guides. Note their dates. Old docs often describe a target the code never reached.
2. **Real tokens**: the CSS theme (Tailwind `@theme`, CSS variables, DaisyUI or other theme config). Record the actual font families, brand colors, text color, radii.
3. **Hard-coded values**: count inline colors and font sizes across the view files (for example `grep -rc "#F5C200" src`). A high count means a token cleanup has to come first, and it decides how risky a color change is.
4. **Theme mode**: is dark mode supported, forced off (`data-theme="light"`), or following the system?
5. **Shared styles**: does one codebase serve several brands, tenants or white-label customers? What does the brand switch change (names, logos) and what does it not (colors, layout)?
6. **Screens**: list every screen a regular user sees and every admin screen. Routes are the fastest source.
7. **Wrappers**: does the app also run inside a native shell (a WebView with an embed flag), on tablets, as a PWA with a service worker? Each is a place where a screen can look different.
8. **Tests that pin the look**: tests asserting colors, class names or HTML snapshots. They will fail on purpose later; note them now.
9. **Ways to run it locally**: dev command, CSS build, local database setup, seed data, and anything in the environment that points at production.

Tell the user the audit in five lines or fewer: current fonts and colors, how far they are from the documented target, theme mode, shared brands, and the number of user and admin screens. Then go to "Lock the look".
