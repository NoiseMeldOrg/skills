# Run it

Two ways. Offer both, recommend one based on the deadline and whether the user will be around.

## Attended (the cycle-orchestration default)

A fresh session per phase, started with "review the newest cycle and start phase N." The agent plans in plan mode, the user confirms, the agent builds, the reviewer agent writes `review.md`, and the user says go before the next phase.

## Unattended with /goal

`/goal` keeps Claude working until a stated condition is met, checked by a small model after each turn. It does not skip permission prompts, so pair it with auto mode. Use it when the user wants the phases built while they are away and will review everything at the end.

Tell the user, in plain words:

- Start a new session **in the repo folder itself**, so the repo's project skills load (a session started in a parent folder may not see them).
- Turn on auto mode (Shift+Tab cycles the modes in Claude Code).
- Paste the goal from `templates/goal.md`, filled in.

The goal text must:

- Name the cycle folder, the phases to run, and the branch to create.
- Pre-approve the plans: where a brief says to ask or wait for a go, pick the recommended option and record it in `log.md`. The reviewer agent's `review.md` stands in for the go between phases.
- Stop the last phase before its deploy step, after building and testing the review kit.
- Define done as files and checks, not feelings: phases built, screenshots saved, the kit works, no new type errors, tests pass on a local database, `log.md` and `review.md` (no open must-fix items) for each phase, `summary.md` updated, all committed on the branch.
- Forbid: pushing, deploying, touching a production database, committing files the repo says never to commit.
- Bound the run: "or after N turns" (200 to 250 for two phases is a reasonable ceiling).

Record in `summary.md` Decisions that the run is unattended and which phases the goal covers.

When the user says the goal finished, read `summary.md`, both `log.md` files and both `review.md` files, check the branch with `git log`, and go to "Review and ship".
