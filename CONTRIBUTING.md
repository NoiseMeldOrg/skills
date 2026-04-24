# Contributing

Thanks for wanting to help. This repo is a Claude Code plugin marketplace publishing skills for document extraction and prose editing. Here's what you need to know to contribute effectively.

## Setup

Clone the repo and activate the git hooks (one-time, per clone):

```bash
git clone https://github.com/NoiseMeldOrg/skills.git
cd skills
git config core.hooksPath .githooks
```

The hooks auto-bump the version and regenerate `CHANGELOG.md` on every commit. See [Versioning](#versioning-and-changelog-automatic--dont-fight-the-hooks) below.

## Testing a skill locally

Symlink the skill into your global `~/.claude/skills/` directory:

```bash
ln -s "$(pwd)/skills/extract-book" ~/.claude/skills/
```

Start a new Claude Code session and the skill will load. Edits to `SKILL.md` or scripts take effect on the next skill invocation — no reinstall needed.

For the Python-based extract skills, install the dependencies:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pdfplumber youtube_transcript_api trafilatura
```

Test each script directly against a sample input (`--dry-run` is your friend) before committing. There are no unit tests — the contract is "the script produces reasonable output for real files, and the `SKILL.md` prose tells Claude how to clean up what it misses."

## Versioning and CHANGELOG (automatic — don't fight the hooks)

- Version is `1.0.<commit-count-on-main>`, rewritten into `.claude-plugin/marketplace.json` by the pre-commit hook.
- `CHANGELOG.md` is regenerated from `git log` by the commit-msg hook.
- **Never hand-edit** `metadata.version` or any entry in `CHANGELOG.md` — both get overwritten on the next commit.
- Check the current version without writing: `./scripts/set_version.sh --check`.

## Commit messages

The first line of every commit becomes a changelog heading; body lines become bullets. Write accordingly:

```
Fix column-bleed detection in extract-study

- Detect three-column layouts using column-width variance
- Fall back to two-column when variance is inconclusive
```

Not:

```
fixed a bug
```

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`, optional `when_to_use`, optional `paths`). Front-load the actual trigger phrases a user would type — Claude under-triggers skills with vague descriptions.
2. If the skill ships a script, add `skills/<name>/scripts/<name>.py`. Scripts are standalone (no shared library), depend on at most one PyPI package, and support `--dry-run` where preview behavior is useful.
3. For domain-heavy skills, put bundled knowledge in `skills/<name>/references/<topic>.md` and cite by path from `SKILL.md`. Keeps the SKILL.md prose lean.
4. Add a `plugins[]` entry to `.claude-plugin/marketplace.json` pointing at `./skills/<name>`. If the skill fits the extraction bundle, add it to `extraction-skills.skills` as well.
5. Update `README.md` with the install block and a short skill description.

## Editing an existing skill

- **`SKILL.md` prose** — free to edit, but trigger descriptions are functional: wording affects whether Claude fires the skill. The README's "Making skills trigger reliably" section explains the model.
- **Scripts** — test against a sample input before committing. The extract skills follow a "dry run, then extract, then post-process with Claude's judgment" pattern; move logic into scripts only when it's deterministic enough to not need Claude's review.
- **Filenames produced by the skills** — all four extract skills default to lowercase kebab-case (e.g., `tom-solid-note-taking-apps.md`). Keep new skill output consistent with that convention.

## What not to do

- Don't hand-edit `metadata.version` in `marketplace.json` or `CHANGELOG.md` entries.
- Don't add emoji to skill content or scripts.
- Don't fork third-party skills into this repo — reference them in the README's "Related skills" section so `npx skills update` keeps working for users.
- Don't skip the hooks (`--no-verify`). If a hook fails, fix the underlying issue; the hooks are load-bearing for the versioning and changelog pipeline.

## Proposing changes

Open a pull request against `main`. Small, single-purpose PRs merge fastest. If the change is structural or the direction is uncertain, open an issue first so we can align before you write the code.

## License

By contributing, you agree your work is licensed under this repo's [MIT license](LICENSE).

## Questions

Open an issue at [github.com/NoiseMeldOrg/skills/issues](https://github.com/NoiseMeldOrg/skills/issues).
