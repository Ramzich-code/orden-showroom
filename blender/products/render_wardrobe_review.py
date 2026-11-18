"""
Wardrobe geometry review (clay): view near the approved image angle + four views.

    blender -b --factory-startup --python blender/products/render_wardrobe_review.py
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

OUT = os.path.abspath(os.path.join(HERE, "..", "renders", "wardrobe_review"))


def render(name):
    s = bpy.context.scene
    s.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] rendered", s.render.filepath)


def main():
    os.makedirs(OUT, exist_ok=True)
    root = bp.build_one("wardrobe")
    rc.assign_clay()
    rc.cyclorama()
    rc.setup_render()
    rc.frame_camera(root, dict(az=20, el=8, lens=50, tz=1.0, res=(1600, 1000)))   # lights
    s = bpy.context.scene

    # 1. near the approved image's angle: almost frontal, slightly from the left, eye ~1.1 m
    t = Vector((0, 0, 1.03))
    rm.add_camera(t + rm.look_dir(14, 2) * 6.5, t, lens=85, res=(900, 1200))
    render("image_angle.png")

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
    c = Vector((0, 0, (bp.WARDROBE["H"] + bp.WARDROBE["legs"]) / 2))
    for name, az, el in (("inspect_front", 0, 0), ("inspect_left", 90, 0), ("inspect_plan", 0, 89.999)):
        rm.add_camera(c + rm.look_dir(az, el) * 5, c, ortho_scale=2.4, res=(1400, 1000))
        render(f"{name}.png")
    s.render.use_freestyle = False
    bpy.data.objects["cyclorama"].hide_render = False
    bg.inputs["Strength"].default_value = 0.6
    t = Vector((0, 0, 1.0))
    rm.add_camera(t + rm.look_dir(32, 12) * 5.2, t, lens=50, res=(1400, 1000))
    render("three_quarter.png")


if __name__ == "__main__":
    main()
