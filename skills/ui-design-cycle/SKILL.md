---
name: ui-design-cycle
description: Run a UI polish or redesign of an existing app as a cycle - audit the current look, lock the design decisions (font, colors, shape, dark mode, which screens first), plan phases with cycle-orchestration, build on a branch (optionally unattended with /goal in auto mode), then review every screen before and after with a side-by-side compare page and the original and new versions running locally, and only then push. Use when the user says "polish the UI", "clean up the design", "redesign the screens", "make the app look finished", "UI design cycle", "design pass before the demo", "compare the old and new UI", or wants Claude to restyle an app to a high standard without changing what it does.
---

# UI design cycle

A UI design cycle changes how an existing app looks, not what it does. It runs as a normal cycle (see `cycle-orchestration`) with four additions that make design work safe to hand to an agent:

1. **An audit before any decision**, so choices are made against what the code really does today.
2. **Locked design decisions**, written down before the first edit.
3. **A branch and a hard "no push" line**, so the live app is untouched until the user approves.
4. **A review kit**: a before-and-after page for every screen and the original and new apps running side by side on the user's machine. The user approves from the kit, not from a description.

## Required input

- The app (repo) and a one-line goal, for example "make the staff screens look finished before the demo".
- A deadline, if there is one. Ask for it; it shapes the phases.

## Skills this one calls

- `cycle-orchestration` for the cycle folder, `summary.md`, phases, reviewer agent and gates. Required.
- `bm-prd-creator` (through cycle-orchestration) for the PRD of a big cycle.
- `impeccable` (or `impeccable:impeccable`) for the design passes: critique, audit, normalize, typeset, polish, adapt. Use it if installed; otherwise apply the same passes by hand.
- The repo's own frontend skill, if it has one (check the repo `CLAUDE.md`).
- `clear-and-concise-humanization` for any copy the redesign touches.

## The process

At the start, show this list with one short sentence per item, then begin step 1.

1. **Start and audit** - `steps/start-and-audit.md`: start the cycle, then measure the current look.
2. **Lock the look** - `steps/lock-the-look.md`: the design questions, one at a time, each with a recommendation.
3. **Plan the phases** - `steps/plan-phases.md`: the standard phase shape and what every phase brief must contain.
4. **Run it** - `steps/run-with-goal.md`: on a branch, phase by phase, or unattended with `/goal` in auto mode.
5. **Review and ship** - `steps/review-and-ship.md`: the user reviews with the kit, flags get fixed, then push and deploy with the user's OK.

## Hard rules

- **Look, not behavior.** No new features, no changed flows, no changed form fields or legal wording. If a fix needs a behavior change, record it as an open question instead.
- **Branch, never main, and never push.** The agent commits on a cycle branch. Pushing and deploying happen only after the user has reviewed with the kit and said go, every time.
- **Local databases only.** Anything run for screenshots or review uses a local database with fake data. Before running anything, check that the app's environment does not point at production; if it does, override it and say so.
- **Before shots before the first edit.** Once code changes, the "before" is gone. Take them first, from the commit the branch starts at.
- **Every shared style is checked everywhere it is shared.** If several brands, tenants or themes share the styles, every screenshot set covers each of them.
- **Write it down.** Decisions go in the cycle's `summary.md`; anything durable (tokens, fonts, rules) goes back into the repo's design docs at the end.

## Templates and references

- `templates/compare.html` - the before-and-after review page. The agent fills in one JSON block; the page does the rest.
- `templates/checklist.md` - the hands-on walkthrough for the local review.
- `templates/goal.md` - the `/goal` text for an unattended run.
- `references/review-kit.md` - what the review kit must do, including the local-database guard.
