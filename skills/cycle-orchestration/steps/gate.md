# Stop at the gate

Report to the user in plain, short sentences:

1. What this phase built, in two or three lines.
2. The review verdict, and any finding still open (must-fix left over, nice-to-haves to decide).
3. What they should look at themselves: a screen to open, a URL, a command to run. Give exact paths and commands.
4. What the next phase is, in one line.

Then ask for one of: **go** (next phase), **fix first** (name what), or **stop here**. Do not start the next phase until the user says go. Record the answer in `summary.md`.

At the end of the last phase, say the cycle is complete and suggest what, if anything, should move out of the cycle into the repo's durable docs (`agent-os/product/`, `CLAUDE.md`).
