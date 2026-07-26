#!/bin/bash
# Shared helpers for the playtest release scripts.
# Sourced, not executed.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_GLOB="labolic-playtest-*.html"

# Highest version number present in the repository root.
latest_version() {
  local n
  n=$(cd "$REPO_ROOT" && ls $VERSION_GLOB 2>/dev/null \
        | sed -n 's/^labolic-playtest-\([0-9]\{1,\}\)\.html$/\1/p' \
        | sort -n | tail -1)
  [ -n "$n" ] || { echo "error: no $VERSION_GLOB found in $REPO_ROOT" >&2; return 1; }
  echo "$n"
}

version_file() { echo "labolic-playtest-$1.html"; }
