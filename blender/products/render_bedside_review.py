"""
Bedside table geometry review (clay): reference-camera view + four views.

    blender -b --factory-startup --python blender/products/render_bedside_review.py
"""
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_products as bp  # noqa: E402
import overlay_bedside as ob  # noqa: E402
import render_clay as rc  # noqa: E402
import render_match as rm  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "renders", "bedside-table_review"))


def render(name):
    s = bpy.context.scene
    s.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] rendered", s.render.filepath)


def main():
    os.makedirs(OUT, exist_ok=True)
    root = bp.build_one("bedside-table")
    rc.assign_clay()
    rc.cyclorama()
    rc.setup_render()
    rc.frame_camera(root, dict(az=40, el=20, lens=50, tz=0.25, res=(1600, 1000)))   # lights
    s = bpy.context.scene

    # 1. the reference photograph's camera (solved), at 2x resolution
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o)
    ob.solved_camera()
    s.render.resolution_x, s.render.resolution_y = ob.W_IMG * 2, ob.H_IMG * 2
    render("photo_camera.png")

    # 2. orthographic front / left / top with edge lines, then a three-quarter
    bpy.data.objects["cyclorama"].hide_render = True
    bg = s.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.92, 0.91, 0.89, 1)
    bg.inputs["Strength"].default_value = 1.0
    s.render.use_freestyle = True
    s.render.line_thickness_mode = "ABSOLUTE"
    s.render.line_thickness = 1.2
    ls = s.view_layers[0].freestyle_settings.linesets[0]
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("lines")
    ls.linestyle.color = (0.08, 0.08, 0.08)
    c = Vector((0, 0, bp.BEDSIDE["H"] / 2))
    for name, az, el in (("inspect_front", 0, 0), ("inspect_left", 90, 0), ("inspect_plan", 0, 89.999)):
        rm.add_camera(c + rm.look_dir(az, el) * 5, c, ortho_scale=1.35, res=(1400, 1000))
        render(f"{name}.png")
    s.render.use_freestyle = False
    bpy.data.objects["cyclorama"].hide_render = False
    bg.inputs["Strength"].default_value = 0.6
    t = Vector((0, 0, 0.24))
    rm.add_camera(t + rm.look_dir(35, 18) * 3.0, t, lens=50, res=(1400, 1000))
    render("three_quarter.png")


if __name__ == "__main__":
    main()
