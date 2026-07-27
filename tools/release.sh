#!/bin/bash
# Point index.html at a version. This is the whole "deploy" step.
#
# index.html is a redirect rather than a copy of the build: a copy would add
# ~600 KB per release and, worse, leave two files that can drift apart. The
# redirect also keeps the versioned filename visible in the address bar, so a
# playtester reporting a bug can say which build they were on.
#
# Usage: tools/release.sh [version]      (default: newest)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
cd "$REPO_ROOT"

ver="${1:-$(latest_version)}"
target=$(version_file "$ver")
[ -f "$target" ] || { echo "error: $target not found" >&2; exit 1; }

cat > index.html <<EOF
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=$target">
<link rel="canonical" href="$target">
<title>Welcome to LABolic!</title>
</head>
<body>
<p>最新版へ移動します: <a href="$target">$target</a></p>
</body>
</html>
EOF

echo "index.html -> $target (v$ver)"

# Superseded builds bounce back here so a refresh cannot strand someone on an
# old version. Must run after index.html is written and must clear the stub
# from the version just released, or the two redirects chase each other.
python3 tools/redirect_stubs.py "$ver"
