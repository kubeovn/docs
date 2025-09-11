#!/bin/bash

# Squash gh-pages branch history to reduce repository size
# 
# Background: mike tool doesn't provide squash option during deployment,
# causing gh-pages directory to grow continuously with each deployment.
# This script needs to be run periodically to compress the branch history.

# Switch to gh-pages branch
git checkout gh-pages

# Create a new root commit with current tree but drop all history
newroot=$(git commit-tree HEAD^{tree} -m "squash: keep current tree, drop history")

# Checkout the new root commit
git checkout $newroot

# Force update gh-pages branch to point to the new root
git branch -f gh-pages "$newroot"

# Switch back to gh-pages branch
git switch gh-pages

# Expire all reflog entries immediately
git reflog expire --expire=now --expire-unreachable=now --all

# Aggressive garbage collection to remove unreachable objects
git gc --prune=now --aggressive

# Force push the squashed branch to remote
git push --force-with-lease origin gh-pages