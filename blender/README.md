# ORDEN — Blender production

Blender 4.5 LTS, run headless with Cycles on the GPU (OptiX).

```bash
BLENDER="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
"$BLENDER" -b --factory-startup --python blender/products/build_products.py   # -> blender/products/<id>.blend
"$BLENDER" -b --factory-startup --python blender/products/render_clay.py      # -> blender/renders/phase1_clay/<id>.png
```

## Model conventions (shared with the website)
- One `.blend` per product: `coffee-table`, `bedside-table`, `wardrobe`.
- Metres, Z up in Blender; the front of each product faces −Y. The glTF exporter converts to Y up.
- A root empty sits at the footprint centre on the floor; each physical component is its own object.
- Object name = component id (`top`, `platform`, `upright`, `drawer-front`, …).
- Each component has a custom property `role` (`body`, `travertine`, `marble`, `base`, `accent`, `metal`, `interior`).
  Finishes swap materials by role only; geometry never changes.
- UVs are world-scale box projections (1 UV unit = 1 m), with wood grain on U.

## Production order
1. Product modelling and materials (`products/`)
2. Individual product renders for approval
3. Showroom environment in Cycles
4. Website integration (optimised GLB + renders)
5. Transitions, interactions, exploded views
6. Desktop and mobile optimisation

Source textures, HDRIs and models go in `blender/assets/` (git-ignored) once approved; see `docs/asset-shortlist.md`.
