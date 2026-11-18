#!/bin/bash
# Re-render the paint-dependent Phase 2 images for bedside table and wardrobe.
B="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
cd "$(dirname "$0")/../.."
for P in bedside-table wardrobe; do
  for job in "signature hero" "signature front" "signature close" "white hero" "black hero"; do
    set -- $job
    "$B" -b --factory-startup --python blender/products/render_product.py -- "$P" "$1" 512 "$2" 2>&1 | grep -E "\[ORDEN\]|Error|Traceback"
  done
done
