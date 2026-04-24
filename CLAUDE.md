# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code plugin marketplace publishing five skills for document extraction and prose editing. There is no application here — each "skill" is a `SKILL.md` (frontmatter + prose Claude reads at session start) plus, for the extraction skills, a single Python script Claude invokes via Bash. The repo's job is to ship those bundles and keep the marketplace manifest in sync.

## Layout

- `.claude-plugin/marketplace.json` — single source of truth for what ships. Each entry under `plugins[]` points at one or more `./skills/<name>` directories. The `extraction-skills` entry is the meta-bundle of the four extract skills.
- `skills/<name>/SKILL.md` — the skill itself. The frontmatter `description` is what Claude matches against when deciding to fire the skill, so changes there affect trigger reliability.
- `skills/<name>/scripts/*.py` — standalone Python scripts the skill's prose tells Claude to run. They have no shared library; each is self-contained and depends on one third-party package (`pdfplumber`, `youtube_transcript_api`, or `trafilatura`).
- `skills/clear-and-concise-humanization/references/` — bundled reference material (Strunk, Wikipedia AI-tells, tiered word lists) the skill cites by path.
- `scripts/` and `.githooks/` — repo-level automation for versioning and changelog (see below).

## Versioning and changelog (automated, do not edit by hand)

Version is `1.0.<commits-on-main>`. The pre-commit hook runs `scripts/set_version.sh`, which rewrites `metadata.version` in `marketplace.json` and stages it. The commit-msg hook runs `scripts/generate_changelog.py`, which regenerates `CHANGELOG.md` from `git log` (plus the pending message) and stages it.

Consequences:
- Never hand-edit `metadata.version` in `marketplace.json` or any entry in `CHANGELOG.md` — both get overwritten on the next commit.
- The first line of every commit message becomes a changelog heading; body lines become bullets. Write commit messages accordingly.
- Hooks live in `.githooks/`, not the default path. Activate them once per clone: `git config core.hooksPath .githooks`.
- `./scripts/set_version.sh --check` prints the version without writing.

## Common tasks

Adding a new skill:
1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`, optional `when_to_use`, optional `paths`). Front-load actual user trigger phrases in `description` — Claude under-triggers skills with vague descriptions.
2. If it ships a script, add `skills/<name>/scripts/<name>.py` and reference it from SKILL.md as `{SKILL_DIR}/scripts/<name>.py`.
3. Add a `plugins[]` entry to `.claude-plugin/marketplace.json` pointing at `./skills/<name>`. If it belongs in the bundle, also add it to `extraction-skills.skills`.
4. Update README.md's installation block and skill description.

Editing an extract script: each `extract_*.py` supports `--dry-run` for preview and writes Markdown to the path given by `-o` (or a default next to the input). Test by running the script directly against a sample file before committing — there are no unit tests in this repo.

## Conventions

- The extract skills follow a "dry run, then extract, then post-process with Claude's judgment" pattern. Don't try to make the scripts perfect — the SKILL.md prose tells Claude to clean up what the script misses (titles, metadata, table artifacts). Move logic into the script only when it's deterministic enough to not need review.
- Skill descriptions and `when_to_use` fields are functional code, not docs. Changing wording changes trigger behavior. The README's "Making skills trigger reliably" section explains the model.
- No emoji in skill content or scripts (per the global writing rules in `~/.claude/CLAUDE.md`).
- Put bundled domain knowledge a skill cites by path in `skills/<name>/references/<topic>.md`. Keeps the SKILL.md prose lean and delegates detail to reference files — easier to maintain, and Claude loads them only when the skill's prose tells it to. Currently used by `clear-and-concise-humanization/references/` (Strunk, signs-of-ai-writing, tiered AI-tell word lists). Good candidates to extend if their SKILL.md prose starts getting heavy: `extract-study` (IMRaD structure, column-bleed heuristics), `extract-book` (chapter-detection patterns).
- Output filenames produced by the extract skills are lowercase kebab-case, identifier-first (e.g., `dugani-2021-lipid-markers-womens-health.md`). Each skill's SKILL.md documents the exact pattern; keep new skills consistent.

## Distribution channels

Three install paths work today, no action needed to keep them working:
- **Claude Code plugin marketplace** — users run `/plugin marketplace add NoiseMeldOrg/skills` then `/plugin install <name>@noisemeld-skills`. Reads `.claude-plugin/marketplace.json`, pins via its `version` field.
- **`npx skills add`** — users run `npx skills add NoiseMeldOrg/skills@<skill> -g -y`. The CLI clones at HEAD and symlinks into `~/.claude/skills/`. No registry submission — any public repo with the right layout works.
- **Symlink install** — documented in README; `ln -s` from a local clone into `~/.claude/skills/`. Updates via `git pull`.

**Anthropic's plugin directory** (`clau.de/plugin-directory-submission`) is a separate path that requires per-plugin submission, not per-marketplace. Each skill would need its own `.claude-plugin/plugin.json`, standalone README, and to pass Anthropic's review for the "Verified" badge. This is significant restructuring — five marketplace entries → five separately submittable plugins. Do not pursue until there's usage signal that justifies the work; the marketplace install path already covers the same users.

**mcpmarket.com** likely auto-crawls public plugin marketplaces, but the submission mechanism is undocumented from what's been verified. Let it index organically.

## Releases

Every commit bumps the version via the hook, but only cut a GitHub release at meaningful milestones (public launch, new skill, breaking change) — never on every commit. The marketplace's `version` field is what `/plugin update` reads; Git tags are only useful for users who want to pin to a specific revision. Use `gh release create v1.0.N` with the changelog entry for that version as the body.
