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

# The link-preview tags (og:*) live here: chat apps and SNS read this page and
# do not follow its refresh to the build.
cat > index.html <<EOF
<!doctype html>
<!--
  Welcome to LABolic!
  Copyright (c) 2026 Toki. All rights reserved.
  ライセンス未設定（全権利留保）。 https://github.com/ShunTokita/welcome-to-LABolic
-->
<html lang="ja">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=$target">
<link rel="canonical" href="$target">
<title>Welcome to LABolic!</title>
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<meta name="apple-mobile-web-app-title" content="LABolic">
<meta name="description" content="金属材料研究を体験するブラウザゲームです。現役の研究者がAIと作りました。">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Welcome to LABolic!">
<meta property="og:title" content="Welcome to LABolic!">
<meta property="og:description" content="金属材料研究を体験するブラウザゲームです。現役の研究者がAIと作りました。">
<meta property="og:url" content="https://shuntokita.github.io/welcome-to-LABolic/">
<meta property="og:image" content="https://shuntokita.github.io/welcome-to-LABolic/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Welcome to LABolic! のロゴと、研究室のキャラクターと装置のドット絵">
<meta name="twitter:card" content="summary_large_image">
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
