#!/bin/bash
# Regenerate every pixel asset and the review sheet, in dependency order.
#
#   floors/walls/devices/       write assets/pixel/
#   sprites/products
#   import_product_art          converts handed-over icon art
#   art-in/final                hand-corrected icons, copied over the lot
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
# Hand-finished icons win over everything: they were corrected dot by dot in
# the browser editor, and re-running them through the importer would undo that
# work. Copied verbatim, never reprocessed.
if ls art-in/final/*.png >/dev/null 2>&1; then
  cp art-in/final/*.png assets/pixel/product/
  echo "final icons: $(ls art-in/final/*.png | wc -l | tr -d ' ') copied verbatim"
fi
python3 tools/pixelart/make_scene.py
python3 tools/pixelart/make_preview.py

echo
echo "publish this file as an Artifact:"
echo "  $PWD/build/pixelart-preview.html"
