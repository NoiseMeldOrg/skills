# /goal text for an unattended run

Fill in the braces, then give the user three steps: start a new session in the repo folder (`cd {repo} && claude`), turn on auto mode (Shift+Tab), and paste the goal.

```
/goal Run the cycle cycles/{cycle-folder} through phases {first} to {last} on a new branch named {branch} (from {base branch}). Follow summary.md, the PRD and each phase prompt.md. The user has pre-approved the plans: where a brief says to ask or wait for a go, pick the recommended option, record it in that phase's log.md, and continue. Between phases, the reviewer agent's review.md stands in for the go. Phase {last} stops before its deploy step: build and test the review kit (review/compare.html, review/run-local.sh, review/checklist.md) instead. Done means: every phase is built, before and after screenshots are saved, the review kit works (every local site loads against local databases only, every image in compare.html loads), the build adds no new type errors, tests pass against a local test database, each phase has log.md and a review.md with no open must-fix items, summary.md is updated, and everything is committed on {branch}. Never git push, never deploy, never touch a production database, never commit {files the repo says never to commit}. Stop when the branch is ready for the user to review, or after {N} turns.
```

Keep it under 4,000 characters. Do not add steps the briefs already contain; the goal names the finish line, the briefs hold the work.
