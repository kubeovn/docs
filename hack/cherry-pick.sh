#!/bin/bash

# Auto Cherry-pick Script
# Automatically cherry-pick specified commit to target branches

set -euo pipefail

# Check parameters
if [ $# -ne 3 ]; then
    echo "Usage: $0 <merge_commit_sha> <target_branches> <pr_number>"
    echo "Example: $0 abc123def 'v1.14,v1.13' 123"
    exit 1
fi

MERGE_COMMIT="$1"
TARGET_BRANCHES="$2"
PR_NUMBER="$3"

echo "Cherry-picking commit $MERGE_COMMIT to branches: $TARGET_BRANCHES (PR #$PR_NUMBER)"

# Get current branch and fetch latest code
CURRENT_BRANCH=$(git branch --show-current)
git fetch origin

# Check if working directory is clean
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: Working directory is not clean. Please commit or stash changes first."
    exit 1
fi

# Verify if merge commit exists
if ! git cat-file -e "$MERGE_COMMIT" 2>/dev/null; then
    echo "ERROR: Merge commit $MERGE_COMMIT does not exist!"
    exit 1
fi

# Split target branches string into array
IFS=',' read -ra BRANCH_ARRAY <<< "$TARGET_BRANCHES"

# Record failed branches
FAILED_BRANCHES=()

# Execute cherry-pick for each target branch
for BRANCH in "${BRANCH_ARRAY[@]}"; do
    BRANCH=$(echo "$BRANCH" | xargs)  # Remove whitespace
    
    echo "Processing branch: $BRANCH"
    
    # Check if remote branch exists
    if ! git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
        echo "❌ Branch $BRANCH does not exist, skipping..."
        FAILED_BRANCHES+=("$BRANCH")
        continue
    fi
    
    # Switch to target branch
    if ! git checkout -B "$BRANCH" "origin/$BRANCH"; then
        echo "❌ Failed to checkout branch $BRANCH"
        FAILED_BRANCHES+=("$BRANCH")
        continue
    fi
    
    # Execute cherry-pick
    if git cherry-pick -x "$MERGE_COMMIT"; then
        # Push to remote branch
        if git push origin "$BRANCH"; then
            echo "✅ Successfully cherry-picked to $BRANCH"
        else
            echo "❌ Push failed for $BRANCH"
            FAILED_BRANCHES+=("$BRANCH")
            git reset --hard HEAD~1  # Rollback
        fi
    else
        echo "❌ Cherry-pick failed for $BRANCH (conflicts)"
        FAILED_BRANCHES+=("$BRANCH")
        git cherry-pick --abort 2>/dev/null || true
    fi
done

# Switch back to original branch
git checkout "$CURRENT_BRANCH"

# Exit with code 1 if there are failed branches
if [ ${#FAILED_BRANCHES[@]} -gt 0 ]; then
    echo "❌ Failed branches: ${FAILED_BRANCHES[*]}"
    echo "Please manually cherry-pick to these branches."
    exit 1
else
    echo "✅ All cherry-picks completed successfully!"
    exit 0
fi
