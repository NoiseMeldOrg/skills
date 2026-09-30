# Run one phase

1. Read the phase brief: `phases/N-slug/prompt.md` for big cycles, the `## Plan` section of `summary.md` for small ones. Read the prior phases' `log.md` files only where this phase builds on them.
2. Plan the phase against the real code before editing (plan mode or equivalent if the harness has one). If the plan would break the brief, stop and ask instead of improvising.
3. Build only this phase's scope. Anything found that belongs to a later phase goes into `summary.md` Open questions, not into the code.
4. Verify as you go: run the tests and the build. When there is a screen, take screenshots (desktop and phone width for web; the simulator for mobile) into `phases/N-slug/screenshots/` (or `cycles/<cycle>/screenshots/` for small cycles).
5. Write `phases/N-slug/log.md` (big cycles only): what was built, files touched, tests run and their results, anything left undone and why. Keep it factual; the reviewer will check it.
6. Set the phase status in `summary.md` to `built, in review`.
