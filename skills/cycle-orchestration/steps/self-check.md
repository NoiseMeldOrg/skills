# Self-check

Before ending the run, check each item and fix any that fail:

- [ ] `summary.md` Status and Next step are true right now.
- [ ] A fresh agent given only "review the newest cycle and continue" could start the right action from `summary.md` without this chat.
- [ ] Every decision locked this session is in a file, and the user was told which one.
- [ ] Every finished phase has a `log.md` and a `review.md` (big cycles), or a checked result in `summary.md` (small cycles).
- [ ] No phase was started without the user's go.
- [ ] Nothing in the app imports or reads from `cycles/`.
- [ ] The cycle folder changes are committed if the repo's rules allow a commit now; otherwise tell the user they are not committed.

End by telling the user the one-sentence prompt to use next time, for example: "Review the newest cycle and start phase 3."
