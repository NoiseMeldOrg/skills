# Review checklist: {cycle name}

Run `./run-local.sh`, then do each step on the original and the new version of each brand. Open the two in side-by-side browser windows at phone width (in Chrome: View > Developer > Developer Tools, then the phone icon, 390 px wide).

| Port | Site |
|---|---|
| :3000 | {brand A, original} |
| :3001 | {brand A, new} |
| :3002 | {brand B, original} |
| :3003 | {brand B, new} |

Sign in as: {demo account and where the password is kept}

## Walkthrough

1. **Sign in.** Good: the logo and the form fit on the screen without scrolling; a wrong password shows a clear message.
2. **Home.** Good: the most used actions are first and obvious; nothing looks unfinished.
3. **{Main screen 2}.** Good: {one line}.
4. **{Main screen 3}.** Good: {one line}.
5. **Complete one task: {task}.** Good: every field is easy to tap; required fields are marked; the confirmation screen is clear.
6. **{Error or empty state}.** Good: it says what happened and what to do next.
7. **Tablet width (820 px) and the native-shell view ({embed flag}).** Good: nothing is cut off, stretched or doubled.

## Things that will not work locally

- {for example: AI answers, email delivery, push notifications}

When done, open `compare.html`, finish the Approve and Flag marks, click "Copy review notes" and paste them to Claude.
