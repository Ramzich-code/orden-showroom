"""
Proof renders for the coffee table's identical slabs.

  slabs_side_by_side.png   the two platforms lifted out and placed next to
                           each other at the same height (panel hidden)
  three_quarter_open.png   assembled table, three-quarter view from slightly
                           above, bright fill so the lower slab reads solid

    blender -b --factory-startup --python blender/products/render_proof.py
"""
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_products as bp  # noqa: E402
import render_clay as rc  # noqa: E402
import render_match as rm  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "renders", "coffee-table_rev7"))


def main():
    root = bp.build_one("coffee-table")
    rc.assign_clay()
    rc.cyclorama()
    rc.setup_render()
    rc.frame_camera(root, dict(az=35, el=25, lens=50, tz=0.15, res=(1600, 1000)))
    s = bpy.context.scene
    world_bg = s.world.node_tree.nodes["Background"]
    world_bg.inputs["Strength"].default_value = 0.6     # brighter fill: no "hollow tray" reading
    objs = {c.name: c for c in root.children}

    # 1. assembled, three-quarter from slightly above
    t = Vector((0.015, 0.02, 0.15))
    rm.add_camera(t + rm.look_dir(35, 24) * 3.3, t, lens=50, res=(1600, 1000))
    s.render.filepath = os.path.join(OUT, "three_quarter_open.png")
    bpy.ops.render.render(write_still=True)

    # 2. the two slabs side by side, same height, panel hidden
    objs["panel"].hide_render = True
    c = bp.COFFEE
    objs["top"].location = (-0.62, 0, c["slab_t"] / 2)
    objs["platform"].location = (0.62, 0, c["slab_t"] / 2)
    t = Vector((0, 0, 0.03))
    rm.add_camera(t + rm.look_dir(0, 89.999) * 4.0, t, ortho_scale=2.8, res=(1600, 900))  # orthographic: equal = equal on screen
    s.render.use_freestyle = True
    s.render.line_thickness_mode = "ABSOLUTE"
    s.render.line_thickness = 1.5
    ls = s.view_layers[0].freestyle_settings.linesets[0]
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("proof_lines")
    s.render.filepath = os.path.join(OUT, "slabs_side_by_side.png")
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] proof renders done")


if __name__ == "__main__":
    main()
