#!/bin/bash
# Regenerate every pixel asset and the review sheet, in dependency order.
#
#   floors/furnace/agt/sprites  write assets/pixel/
#   make_scene                  composes those into build/lab-scene*.png
#   make_preview                inlines everything into one reviewable HTML
#
# Usage: tools/pixelart/build.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

for stage in floors furnace agt sprites; do
  python3 "tools/pixelart/$stage.py"
done
python3 tools/pixelart/make_scene.py
python3 tools/pixelart/make_preview.py

echo
echo "publish this file as an Artifact:"
echo "  $PWD/build/pixelart-preview.html"
