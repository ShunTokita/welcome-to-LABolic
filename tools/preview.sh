#!/bin/bash
# Build a self-contained preview of a version, ready to publish as an Artifact.
#
# Artifact pages are single files behind a CSP that blocks every external
# host, so the assets/ directory has to travel inside the HTML. Output lands
# in build/ (git-ignored) — it is roughly 4.5 MB and regenerated on demand,
# so it never belongs in a commit.
#
# Usage: tools/preview.sh [version]      (default: newest)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
cd "$REPO_ROOT"

ver="${1:-$(latest_version)}"
src=$(version_file "$ver")
[ -f "$src" ] || { echo "error: $src not found" >&2; exit 1; }

mkdir -p build
python3 tools/build_standalone.py "$src" "build/inlined-v$ver.html"
python3 tools/prep_artifact.py "build/inlined-v$ver.html" "build/artifact-v$ver.html"

echo
echo "publish this file as an Artifact:"
echo "  $REPO_ROOT/build/artifact-v$ver.html"
