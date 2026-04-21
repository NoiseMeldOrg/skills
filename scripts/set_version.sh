#!/usr/bin/env bash
# set_version.sh — Auto-version marketplace.json from git commit count.
#
# Versioning scheme (mirrors rapture-ios):
#   Main branch:   1.0.<commit-count>
#   Other branch:  1.0.<base-commits>+<branch-commits>-<branch>
#   No git:        1.0.dev
#
# The commit count includes the commit being made (count + 1) when
# called from a pre-commit hook, since the commit hasn't landed yet.
#
# Version 1.0.N means: this is the Nth commit on main. To find the
# exact code for any version, run: git log --oneline | head -N
#
# Usage:
#   ./scripts/set_version.sh          # auto-detect context
#   ./scripts/set_version.sh --check  # print version without writing

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"

MAJOR=1
MINOR=0

if ! git -C "$REPO_ROOT" rev-parse --git-dir &>/dev/null; then
    echo "1.0.dev"
    exit 0
fi

BRANCH=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
MAIN_COMMITS=$(git -C "$REPO_ROOT" rev-list --count main 2>/dev/null || echo "0")

if [[ "$BRANCH" == "main" ]]; then
    # +1 because this runs in pre-commit, before the commit lands
    if [[ "${GIT_PRE_COMMIT:-}" == "1" ]]; then
        PATCH=$((MAIN_COMMITS + 1))
    else
        PATCH=$MAIN_COMMITS
    fi
    VERSION="$MAJOR.$MINOR.$PATCH"
else
    BRANCH_COMMITS=$(git -C "$REPO_ROOT" rev-list --count main..HEAD 2>/dev/null || echo "0")
    SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '-')
    VERSION="$MAJOR.$MINOR.$MAIN_COMMITS+$BRANCH_COMMITS-$SAFE_BRANCH"
fi

if [[ "${1:-}" == "--check" ]]; then
    echo "$VERSION"
    exit 0
fi

if [[ ! -f "$MARKETPLACE" ]]; then
    echo "Error: $MARKETPLACE not found" >&2
    exit 1
fi

# Update version in marketplace.json using Python (portable JSON editing)
python3 -c "
import json, sys
path = sys.argv[1]
version = sys.argv[2]
with open(path) as f:
    data = json.load(f)
data['metadata']['version'] = version
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" "$MARKETPLACE" "$VERSION"

# Stage the updated file so it's included in the commit
git -C "$REPO_ROOT" add "$MARKETPLACE"

echo "$VERSION"
