---
name: cycle-orchestration
description: Run any job that needs more than one agent session as a dated "cycle" - make the cycle folder with a living summary.md, size the job, plan it (calling bm-prd-creator for big builds), run it phase by phase with a separate reviewer agent and a human go/no-go between phases, and keep summary.md current so a fresh agent can pick up from one sentence. Use when the user says "start a cycle", "new cycle", "plan this project", "continue the cycle", "pick up the cycle", "review the newest cycle and start phase N", "go to the next phase", or "lock it", or starts a multi-session feature, redesign, strategy or content job. Does not handle one-sitting tasks.
---

# Cycle orchestration

A cycle is one job with a start and an end: a feature, a redesign, a strategy session, a piece of content. Every cycle lives in its own dated folder, and every decision and every bit of progress goes into files in that folder. Nothing important lives only in a chat, so any fresh agent can continue the work by reading the folder.

## Required input

- **A new job** (a short description of what to build or decide), or **an existing cycle to continue** (its name, or "the newest cycle").

If the user gave neither, ask for it before doing anything else.

## Where cycles live

- Folder: `cycles/YYYY-MM-DD-short-slug/` at the root of the repo the work is about (the code repo for product work; the content or business repo for other work).
- Every cycle has a `summary.md`. Everything else is added only when the job needs it.
- Big cycles look like this:

```
cycles/2026-10-02-bereavement-module/
├── summary.md
├── prd.md  (and/or prd.html)
└── phases/
    ├── 1-data-model/
    │   ├── prompt.md       # the phase brief
    │   ├── log.md          # what the builder did
    │   ├── review.md       # what the reviewer checked, with evidence
    │   └── screenshots/
    └── 2-staff-screens/…
```

## The process

At the start of every run, show this list with one short sentence per item, then begin step 1 at once without asking permission.

1. **Find or start the cycle** - `steps/find-or-start.md`: open the cycle to continue, or create the folder and `summary.md` for a new one.
2. **Size the job** - `steps/size.md`: recommend small or big and get the user's confirmation. New cycles only.
3. **Plan** - `steps/plan.md`: small jobs get a short plan in `summary.md`; big jobs get a PRD and phase folders through bm-prd-creator. New cycles only.
4. **Run one phase** - `steps/run-phase.md`: build the current phase from its brief and log what was done.
5. **Review** - `steps/review.md`: a separate reviewer agent checks the phase and writes `review.md`; fix what it finds.
6. **Stop at the gate** - `steps/gate.md`: report to the user and wait for "go" before the next phase.
7. **Update summary.md** - `steps/update-summary.md`: record where things stand, the next step and what went wrong.
8. **Self-check** - `steps/self-check.md`: confirm a fresh agent could continue from `summary.md` alone.

When continuing a cycle whose plan already exists, go from step 1 straight to step 4.

## Hard rules

- **"Lock it" means write it down.** When the user says "lock it", "lock that in" or similar, write the decision to a file at once: the cycle's `summary.md` Decisions list, or the repo's durable docs (`agent-os/product/`, `CLAUDE.md`) when the decision outlives the cycle. Say which file.
- **Only the current cycle is live.** Do not read older cycle folders unless the user points to one. Old plans describe decisions the project may have moved away from.
- **One phase per go.** Never start the next phase without the user's "go", even when the work looks fine.
- **Files over chat.** Anything a future agent needs goes into the cycle folder before the run ends.
- **Templates:** `templates/summary.md` for every new cycle, `templates/review.md` for every review.

## Scope

This skill does not handle one-sitting tasks, replace bm-prd-creator's interview, or move old `_build_plan/` folders; those stay as they are.
