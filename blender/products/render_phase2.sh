#!/bin/bash
# Phase 2 product renders (final quality). Usage: bash blender/products/render_phase2.sh <product>
B="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
P=${1:-coffee-table}
cd "$(dirname "$0")/../.."
for job in "signature hero" "signature front" "signature close" "white hero" "black hero" "oak hero"; do
  set -- $job
  "$B" -b --factory-startup --python blender/products/render_product.py -- "$P" "$1" 512 "$2" 2>&1 | grep -E "\[ORDEN\]|Error|Traceback"
done
