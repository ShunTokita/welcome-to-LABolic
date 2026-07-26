#!/bin/bash
# Start the next playtest version: copy the newest build and bump its number.
#
# The version appears in two places that must stay in step — the filename and
# the "Beta vNN" suffix in <title>. A filename mistake shows up immediately as
# a broken link; a stale title does not, so the bump is scripted rather than
# done by hand.
#
# Usage: tools/new-version.sh
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
cd "$REPO_ROOT"

cur=$(latest_version)
next=$((cur + 1))
src=$(version_file "$cur")
dst=$(version_file "$next")

[ -e "$dst" ] && { echo "error: $dst already exists" >&2; exit 1; }

cp "$src" "$dst"

# Fail loudly if the title does not carry the expected marker: silently
# shipping a build labelled with the previous version is the exact mistake
# this script exists to prevent.
if ! grep -q "Beta v$cur" "$dst"; then
  rm -f "$dst"
  echo "error: '<title> ... Beta v$cur' not found in $src — title format changed?" >&2
  exit 1
fi
sed -i "s/Beta v$cur/Beta v$next/g" "$dst"

echo "created $dst (v$cur -> v$next)"
grep -oE '<title>[^<]*</title>' "$dst"
echo
echo "next: edit $dst, then run tools/preview.sh"
