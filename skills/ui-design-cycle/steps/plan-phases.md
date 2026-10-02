# Plan the phases

## The standard shape

Propose this, adjusted to the deadline:

1. **Foundation and first impression**: the shared tokens (colors, type, radii, spacing), hard-coded values moved onto them, the shared components (buttons, inputs, cards, headings, header, navigation), and the first screens anyone sees (sign-in, home).
2. **The rest of the user screens, plus the review kit**: every remaining user screen, the device and wrapper check (phone, tablet, inside the native shell), and the review kit. This phase stops before deploy; the user reviews with the kit, then says go.
3. **Admin or secondary screens to match**: the same tokens and components on the back-office side, with its own before and after shots and its own review.

If the deadline is tight, phases 1 and 2 must fit before it; phase 3 can follow. If there is time, a separate review-kit phase is fine.

## What every phase brief must contain

Patch each `phases/N-slug/prompt.md` (written by bm-prd-creator) so the Context and Task sections include:

- **Where to read**: `summary.md`, the PRD's phase section and "The look, locked", the previous phase's `log.md` and `review.md`, the repo `CLAUDE.md`, the design docs from the audit.
- **Skills**: the repo's frontend skill, `impeccable`, `clear-and-concise-humanization`.
- **Exact files**: the theme file, the layout file, and the view files for this phase's screens, with the hard-coded color counts from the audit.
- **The branch**: work on the cycle branch (for example `design-polish`), never main.
- **Before shots first**: at phone width (390 px) and any other target widths (tablet 820 px, wide 1180 px), inside any native-shell embed mode, for every brand, saved in the phase's `screenshots/` before the first edit. Matching "after" shots at the end.
- **Checks**: the build and type check (compare the error count to the starting count, add none), the tests against a local test database only, and updated look-pinning tests (change the expected values on purpose; never delete the check).
- **Gotchas from the audit**: service worker caches to bump after CSS changes, files that must not be committed, environment values that point at production.
- **No push, no deploy**: commit in small commits on the branch; stop for the user.
- **Fallback order**: if time runs short, which screens finish first, and that skipped work goes in `log.md`.

Phase 2's brief also gets the review kit task from `references/review-kit.md`, placed before any deploy step, with deploy gated on the user's review.

End every brief with the cycle-orchestration line: "When done, write `log.md` in this folder, then stop for review. Do not start the next phase."
