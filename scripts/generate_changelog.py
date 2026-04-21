#!/usr/bin/env python3
"""Generate CHANGELOG.md from git log.

Each commit on main gets an entry: ## 1.0.N — first line of message
with any remaining body lines as bullets underneath.

When a pending commit message file is passed as argv[1], it appears
as the newest entry (version N+1) so the CHANGELOG is never behind.

Usage:
    python generate_changelog.py                       # from git log only
    python generate_changelog.py .git/COMMIT_EDITMSG   # include pending commit
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


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


def main():
    total = int(git("rev-list", "--count", "main") or "0")
    commits = get_commits()

    pending_msg_file = sys.argv[1] if len(sys.argv) > 1 else None
    pending = None
    if pending_msg_file:
        subj, body = read_pending_message(pending_msg_file)
        if subj:
            pending = (subj, body)

    lines = []
    lines.append("# Changelog")
    lines.append("")
    lines.append("Version `1.0.N` = the Nth commit on `main`. To check out any version:")
    lines.append("")
    lines.append("```bash")
    lines.append("git log --oneline main   # find the commit")
    lines.append("git checkout <hash>      # check it out")
    lines.append("```")
    lines.append("")

    # Pending commit (not yet in git log)
    if pending:
        version_num = total + 1
        lines.append(f"## 1.0.{version_num}")
        lines.append("")
        lines.append(pending[0])
        if pending[1]:
            lines.append("")
            for bl in pending[1]:
                lines.append(f"- {bl}")
        lines.append("")

    # Existing commits: newest is version total, oldest is version 1
    for i, (subject, body) in enumerate(commits):
        version_num = total - i
        if version_num < 1:
            break
        lines.append(f"## 1.0.{version_num}")
        lines.append("")
        lines.append(subject)
        if body:
            lines.append("")
            for bl in body:
                lines.append(f"- {bl}")
        lines.append("")

    CHANGELOG.write_text("\n".join(lines) + "\n")

    # Stage the changelog
    subprocess.run(["git", "-C", str(REPO_ROOT), "add", str(CHANGELOG)])


if __name__ == "__main__":
    main()
