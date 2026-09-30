# Update summary.md

`summary.md` is the note one agent leaves for the next. Rewrite it so it is true right now; do not just append.

- **Status:** one line: which phase, and its state (not started / building / in review / waiting for go / done).
- **Next step:** the exact next action, specific enough that "do the next step" is a full instruction.
- **Phases:** update each phase's status and link its folder.
- **Decisions:** add anything locked this session, with the date. Remove nothing; mark reversed decisions as reversed.
- **What went wrong:** hiccups a future agent would otherwise hit again (a flaky command, a wrong assumption, a tool that failed), and the fix.
- **Open questions:** things waiting on the user or on a later phase.

Keep it scannable. Put long detail in the phase `log.md` and link to it.
