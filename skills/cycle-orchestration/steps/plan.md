# Plan

Do not start building while planning. The output of this step is files, not code.

## Small cycle

Write a `## Plan` section in `summary.md`: 3 to 7 numbered steps, what "done" looks like, and how it will be checked (a test, a screenshot, a read-through). Ask any questions that would change the plan, one at a time, recommending an answer each time. Treat the whole small cycle as one phase.

## Big cycle

1. Run the **bm-prd-creator** skill with the user's description as the brain dump. Let its interview run as normal. If it is not installed, tell the user it comes from `github.com/buildermethods/bm-skills`, and offer to write `prd.md` and the phase prompts directly instead: what the job builds, what is out of scope, the data it needs, and one `prompt.md` per phase with its scope and a "done when" line.
2. Redirect its output into the cycle folder:
   - Write its PRD to `cycles/<cycle>/prd.md` (and/or `prd.html`), not `_build_plan/`.
   - Write each milestone to `cycles/<cycle>/phases/N-slug/prompt.md`, not `_build_plan/milestones/`. Each milestone is one phase.
   - In every prompt, change `_build_plan/` paths to the cycle's paths, and change `milestone-log.md` to `log.md`.
   - Drop its "temporary, delete after build-out" disclaimer. Cycle folders are kept as history.
   - Skip its `## _build_plan/` note for `CLAUDE.md`; the `## cycles/` note covers it.
3. Patch the Context section of every phase `prompt.md` so the building agent reads the repo's real truth: the repo `CLAUDE.md`, the project skills that apply, the exact files the phase will touch, and any existing code to copy the pattern from. The PRD says what to build; the code says how.
4. Add to the end of every phase `prompt.md`: "When done, write `log.md` in this folder, then stop for review. Do not start the next phase."
5. Fill in the `## Phases` list in `summary.md` with each phase name and status `not started`, and set Next step to "Phase 1".
