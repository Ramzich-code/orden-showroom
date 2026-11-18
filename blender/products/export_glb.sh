#!/bin/bash
# Bake + export the product GLBs. Cycles 4.5 crashes now and then while
# syncing meshes for a bake (EXCEPTION_ACCESS_VIOLATION in ccl::create_mesh),
# so each product is retried a few times.   Usage: bash blender/products/export_glb.sh [ids...]
B="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
cd "$(dirname "$0")/../.."
for pid in ${@:-coffee-table bedside-table wardrobe sofa headboard-shelf shoe-bench}; do
  for attempt in 1 2 3 4 5; do
    if "$B" -b --factory-startup --python blender/products/export_glb.py -- "$pid" 2>&1 | grep -E "\[ORDEN\]" | tee /dev/stderr | grep -q "floor shadow card"; then
      break
    fi
    echo "[ORDEN] $pid: Blender crashed, retry $attempt" >&2
  done
done
