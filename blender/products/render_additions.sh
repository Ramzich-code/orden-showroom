#!/bin/bash
# Studio renders (Signature) of the 2026-11-18 additions. Usage: bash blender/products/render_additions.sh [samples]
B="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
S=${1:-512}
cd "$(dirname "$0")/../.."
for pid in sofa headboard-shelf shoe-bench; do
  for view in hero front close; do
    "$B" -b --factory-startup --python blender/products/render_product.py -- "$pid" signature "$S" "$view" 2>&1 | grep -E "\[ORDEN\]|Error|Traceback"
  done
done
