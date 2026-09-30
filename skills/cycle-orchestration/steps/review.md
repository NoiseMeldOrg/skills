# Review

The builder never reviews its own work. Hand the review to a separate agent: a subagent if the harness has one, otherwise a fresh session given only this instruction and the paths.

## Instruct the reviewer

Give the reviewer:
- The phase brief (`prompt.md`, or the Plan in `summary.md` for a small cycle) and `log.md`.
- The diff for this phase (`git diff` against the commit before the phase started).
- The screenshots folder, if there is one.
- This task: "Check that the work does what the brief says and nothing it forbids. Run the tests and the build yourself. For screens, open them and compare against the brief and screenshots at desktop and phone width. Do not trust the log; check it. Write `review.md` in the phase folder from `templates/review.md`. Mark each finding must-fix or nice-to-have, with the evidence."

## Close the loop

1. Fix every must-fix finding, then send the reviewer back to recheck only those. Repeat until none remain, up to three rounds.
2. If must-fix findings remain after three rounds, stop and put them in front of the user at the gate.
3. Leave nice-to-have findings in `review.md` for the user to decide at the gate.
4. Keep `review.md` final: verdict, what was checked, evidence, findings with their status.
