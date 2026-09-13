#!/bin/bash
# Regenerate every pixel asset and the review sheet, in dependency order.
#
#   floors/walls/devices/       write assets/pixel/
#   sprites/products
#   make_scene                  composes those into build/lab-scene*.png
#   make_preview                inlines everything into one reviewable HTML
#
# Usage: tools/pixelart/build.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

for stage in floors walls devices sprites products; do
  python3 "tools/pixelart/$stage.py"
done
# Externally drawn Discovery icons win over the ones products.py draws, so the
# import has to come after it. Skipped when nothing has been handed over.
if ls art-in/product/*.png >/dev/null 2>&1; then
  python3 tools/pixelart/import_product_art.py art-in/product --size 64
fi
python3 tools/pixelart/make_scene.py
python3 tools/pixelart/make_preview.py

echo
echo "publish this file as an Artifact:"
echo "  $PWD/build/pixelart-preview.html"
