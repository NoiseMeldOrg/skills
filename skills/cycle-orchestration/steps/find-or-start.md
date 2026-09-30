# Find or start the cycle

## Continuing a cycle

1. List `cycles/` in the repo. Folder names start with a date, so the newest sorts last.
2. Open the cycle the user named, or the newest one if they said "the newest cycle" or gave no name.
3. Read its `summary.md` first. Then read only what the next step needs: the PRD, and the current phase's `prompt.md`, `log.md` and `review.md`.
4. Tell the user in two lines what the cycle is and what the summary says is next.

## Starting a new cycle

1. Pick the repo. Product work goes in that product's code repo. Strategy or content work goes in the repo that holds that business or content. If it is unclear, recommend one and confirm.
2. Name the folder `cycles/YYYY-MM-DD-short-slug/` using today's date and 2 to 4 words from the job.
3. Copy `templates/summary.md` into it and fill in the Goal from the user's description. Leave the other sections short; they grow as the cycle runs.
4. If the repo's `CLAUDE.md` (or `AGENTS.md`) has no `## cycles/` section, add this at the bottom:

```markdown
## cycles/

`cycles/` holds dated planning folders, one per job (PRD, phase briefs, logs, reviews). They are history and guidance, not code: nothing in the app may import or depend on them. Only the cycle you were pointed at is live. Do not read older cycles unless asked; their decisions may be out of date.
```
