# The review kit

Built in the cycle folder, `cycles/<cycle>/review/`, never in app code. Three files. The user approves the redesign from these, so test them as carefully as the redesign itself.

## 1. compare.html

Start from `templates/compare.html`. Fill in only the JSON block at the top (`<script id="manifest" type="application/json">`); the page renders everything from it, and it opens straight from disk with no server.

Manifest fields:

- `title`, `cycle`: shown in the header. `cycle` also keys the saved review state, so use the cycle folder name.
- `notice` (optional): one line shown under the header, for example "Ask cannot answer locally; its after shots come from the live demo."
- `variants`: one entry per way a screen is shot, `{ "id": "brandA-390", "label": "Brand A, phone" }`. Typical set: each brand at 390 px, at 820 px, and inside the native-shell embed.
- `screens`: one entry per screen, in the order a user meets them:
  - `id` (unique), `group` (Sign-in, Home, Forms...), `name`
  - `changed`: one or two plain-language lines on what changed and why
  - `shots`: an object keyed by variant id, each `{ "before": "relative/path.png", "after": "relative/path.png" }`. Paths are relative to `compare.html`. Leave a variant out if the screen does not exist there.

Before shots come from the commit the branch started at; after shots from the branch head. Keep file names predictable: `screenshots/<variant>/<screen>-before.png` and `-after.png`.

The page gives the user: approve / flag / unreviewed per screen, a note per screen, counts at the top, filters (all, flagged, unreviewed), side-by-side or a "flip" view that swaps before and after in one spot, a variant picker, and a "Copy review notes" button that puts every flag and note on the clipboard as plain text. State is saved in the browser per cycle.

Test it: open the file, check every image loads (the page lists broken images at the top), approve one screen, reload, confirm it stuck.

## 2. run-local.sh

One command that runs the original and the new app side by side on the user's machine, one port per brand and version. For one brand: original on :3000, new on :3001. For two brands: :3000 to :3003. Print the URLs and the demo sign-in when it starts.

Requirements:

- The original runs from a git worktree of the commit the branch started at, placed outside the repo folder. Create it if missing; leave it for reuse.
- Every server uses a local database with fake seed data. Create and seed one database per version if needed, using the repo's own bootstrap and seed commands.
- **Refuse to start** if any database URL in the effective environment is not local. App `.env` files often point at production, and dev servers load them automatically. Override the URL on the command line and check it before starting anything:

```bash
assert_local_db() {
  case "$1" in
    *@localhost:*|*@localhost/*|*@127.0.0.1:*|*@127.0.0.1/*|*@\[::1\]*) ;;
    *) echo "Refusing to start: database URL is not local: ${1%%@*}@..." >&2; exit 1 ;;
  esac
}
```

- Features that need outside services (AI answers, email, push) should fail politely or be switched off locally. Never copy production keys into the script. Say what will not work on the review page's notice line.
- `--stop` stops every server the script started and nothing else. Track the process ids in a file in the review folder.
- Re-running the script while servers are up restarts them cleanly.

Test it: run it, load every port, sign in on each, run `--stop`, confirm the ports are free.

## 3. checklist.md

Start from `templates/checklist.md`. Fill in the real flows: sign in with the demo account, the main screens, one complete task (submit a form, finish a purchase), and the error states worth seeing. Each step gets one line on what "good" looks like.
