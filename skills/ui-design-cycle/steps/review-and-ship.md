# Review and ship

## The user reviews

Give the user three steps, with exact commands:

1. Open `review/compare.html` (it opens straight from disk). Every screen, before and after, for each brand and width. They tick Approve or Flag and add a note per screen. A "Copy review notes" button collects every flag and note as text.
2. Run `review/run-local.sh` and click through the original and new apps side by side, using `review/checklist.md`.
3. Paste the copied review notes back into the chat.

## Fix the flags

For each flag: fix it on the branch, retake its after shot, update its entry in `compare.html`, and reset that screen to unreviewed so the user looks again. Log the fixes in the phase's `log.md` under "Review fixes". Repeat until there are no flags.

If a flag asks for a behavior change or something out of scope, say so, record it under Open questions in `summary.md`, and move on.

## Ship, with the user's OK at each step

1. Ask before merging the branch to main and before every push. Say what the push will redeploy.
2. Deploy any service that does not auto-deploy, following the repo's runbook.
3. Check the live site at phone width through the main flows. Save live screenshots in the phase folder.
4. Update `summary.md`: status, what shipped, what went wrong.

## Close the cycle

After the last phase, move durable decisions (final tokens, font, color values, shape rule, theme mode) into the repo's design docs and the `CLAUDE.md` design section, and note in `summary.md` which doc now holds them. Note any guide or help pages with screenshots that are now out of date.

Ask the user one question to improve this skill: what was slow or confusing in this run? If the answer is general (not about one app), suggest the edit to this skill.
