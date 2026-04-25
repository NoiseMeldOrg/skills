#!/usr/bin/env python3
"""Generate CHANGELOG.md from git log, preserving hand-edited entries.

Each commit on main gets an entry: ## 1.0.N — first line of message
with any remaining body lines as bullets underneath.

Existing entries in CHANGELOG.md are preserved verbatim. Only entries that
don't yet exist (the pending commit, or any version missing from the file)
are written from `git log`. This means once an entry is in the file, you
can polish it and the hook won't clobber your edits on the next commit.

If you amend a past commit's message and want the changelog to pick up the
new wording, delete that version's section from CHANGELOG.md first; the
generator will regenerate it from `git log`.

When a pending commit message file is passed as argv[1], it appears
as the newest entry (version N+1) so the CHANGELOG is never behind.

Usage:
    python generate_changelog.py                       # from git log only
    python generate_changelog.py .git/COMMIT_EDITMSG   # include pending commit
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# Matches a version heading like "## 1.0.42" (trailing whitespace OK).
_VERSION_HEADING = re.compile(r"^## 1\.0\.(\d+)\s*$")


def git(*args):
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + list(args),
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def get_commits():
    """Return list of (subject, body_lines) from newest to oldest."""
    log = git("log", "--format=%s%n%b%n---END---", "main")
    commits = []
    current_subject = None
    current_body = []

    for line in log.splitlines():
        if line == "---END---":
            if current_subject is not None:
                commits.append((current_subject, current_body))
            current_subject = None
            current_body = []
            continue

        if current_subject is None:
            current_subject = line
        else:
            stripped = line.strip()
            if stripped and not stripped.startswith("Co-Authored-By:"):
                current_body.append(stripped)

    if current_subject is not None:
        commits.append((current_subject, current_body))

    return commits


def read_pending_message(path):
    """Read a commit message file, stripping comments and Co-Authored-By."""
    text = Path(path).read_text()
    lines = [l for l in text.splitlines()
             if not l.startswith("#") and not l.startswith("Co-Authored-By:")]

    # First non-empty line is the subject
    subject = None
    body = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if subject is None:
            subject = stripped
        else:
            body.append(stripped)

    return subject, body


def parse_existing_entries(path):
    """Parse CHANGELOG.md into {version_int: section_text}.

    Each section_text starts with the `## 1.0.N` heading and runs up to
    (but not including) the next version heading or EOF, with trailing
    blank lines stripped. Lines before the first version heading
    (the file's intro/header) are ignored.
    """
    if not path.exists():
        return {}

    sections = {}
    current_version = None
    current_lines = []

    for line in path.read_text().splitlines():
        match = _VERSION_HEADING.match(line)
        if match:
            if current_version is not None:
                sections[current_version] = "\n".join(current_lines).rstrip()
            current_version = int(match.group(1))
            current_lines = [line]
        elif current_version is not None:
            current_lines.append(line)

    if current_version is not None:
        sections[current_version] = "\n".join(current_lines).rstrip()

    return sections


def format_entry(version_num, subject, body):
    """Return a list of lines for a freshly generated changelog entry."""
    lines = [f"## 1.0.{version_num}", "", subject]
    if body:
        lines.append("")
        for bullet in body:
            lines.append(f"- {bullet}")
    return lines


def main():
    total = int(git("rev-list", "--count", "main") or "0")
    commits = get_commits()
    existing = parse_existing_entries(CHANGELOG)

    pending_msg_file = sys.argv[1] if len(sys.argv) > 1 else None
    pending = None
    if pending_msg_file:
        subj, body = read_pending_message(pending_msg_file)
        if subj:
            pending = (subj, body)

    out = []
    out.append("# Changelog")
    out.append("")
    out.append("Version `1.0.N` = the Nth commit on `main`. To check out any version:")
    out.append("")
    out.append("```bash")
    out.append("git log --oneline main   # find the commit")
    out.append("git checkout <hash>      # check it out")
    out.append("```")
    out.append("")

    # Pending commit (not yet in git log) -- always freshly generated; the
    # entry doesn't exist yet, and the hook needs it to land in this commit.
    if pending:
        version_num = total + 1
        out.extend(format_entry(version_num, pending[0], pending[1]))
        out.append("")

    # Existing commits: newest is version `total`, oldest is version 1.
    # Preserve any entry already in CHANGELOG.md verbatim; only generate
    # entries for versions that don't have one yet.
    for i, (subject, body) in enumerate(commits):
        version_num = total - i
        if version_num < 1:
            break
        if version_num in existing:
            out.append(existing[version_num])
        else:
            out.extend(format_entry(version_num, subject, body))
        out.append("")

    CHANGELOG.write_text("\n".join(out) + "\n")

    # Stage the changelog
    subprocess.run(["git", "-C", str(REPO_ROOT), "add", str(CHANGELOG)])


if __name__ == "__main__":
    main()
