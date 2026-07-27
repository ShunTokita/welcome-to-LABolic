#!/bin/bash
# Sanity-check a version before release.
#
# Catches the failures that are invisible until someone plays the build: an
# asset referenced but never committed, a title left on the previous number,
# or an index.html pointing at a file that no longer exists.
#
# Usage: tools/check.sh [version]      (default: newest)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
cd "$REPO_ROOT"

ver="${1:-$(latest_version)}"
src=$(version_file "$ver")
[ -f "$src" ] || { echo "error: $src not found" >&2; exit 1; }
fail=0

# 1. Every referenced asset exists.
missing=0
for p in $(grep -oE "assets/[A-Za-z0-9_/.-]+" "$src" | sort -u); do
  [ -f "$p" ] || { echo "MISSING ASSET: $p"; missing=1; fail=1; }
done
[ $missing -eq 0 ] && echo "OK   assets: all references resolve"

# 2. Title matches the filename's version.
title=$(grep -oE '<title>[^<]*</title>' "$src" | head -1)
if echo "$title" | grep -q "Beta v$ver\b"; then
  echo "OK   title: $title"
else
  echo "MISMATCH title: expected 'Beta v$ver', got $title"; fail=1
fi

# 3. Untracked assets would 404 once pushed, even though they work locally.
untracked=$(git ls-files --others --exclude-standard assets 2>/dev/null || true)
if [ -n "$untracked" ]; then
  echo "UNTRACKED (would 404 after push):"; echo "$untracked" | sed 's/^/       /'; fail=1
else
  echo "OK   git: no untracked assets"
fi

# 4. index.html points somewhere real.
if [ -f index.html ]; then
  dest=$(grep -oE 'url=[A-Za-z0-9_.-]+\.html' index.html | head -1 | cut -d= -f2)
  if [ -z "$dest" ]; then
    echo "NOTE index.html: no redirect target found (is it still a full copy?)"
  elif [ -f "$dest" ]; then
    echo "OK   index.html -> $dest"
  else
    echo "BROKEN index.html -> $dest (file does not exist)"; fail=1
  fi
fi

# 5. Redirect stubs: exactly the build index.html points at must be stub-free.
#    If the live version kept its stub, it would bounce to index.html, which
#    bounces straight back — an unbreakable loop on the public entry point.
if [ -f index.html ] && [ -n "${dest:-}" ]; then
  loop=0
  for f in $VERSION_GLOB; do
    has=$(grep -c 'LABOLIC-REDIRECT-START' "$f" || true)
    if [ "$f" = "$dest" ] && [ "$has" -ne 0 ]; then
      echo "REDIRECT LOOP: $f is live but still redirects to index.html"; loop=1; fail=1
    elif [ "$f" != "$dest" ] && [ "$has" -eq 0 ]; then
      echo "NOTE $f has no redirect stub (pinned for rollback?)"
    fi
  done
  [ $loop -eq 0 ] && echo "OK   redirect: live build ($dest) is stub-free"
fi

echo
[ $fail -eq 0 ] && echo "check passed (v$ver)" || { echo "check FAILED (v$ver)"; exit 1; }
