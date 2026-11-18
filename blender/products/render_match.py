"""
Coffee table geometry review against the reference photograph.

  1. match.png        clay render from a camera solved to the reference view
                      (elevation ~25 deg, azimuth ~38 deg, long lens), same
                      pixel size as the photo so the two can be overlaid
  2. inspect_*.png    orthographic front / left side / plan views

    blender -b --factory-startup --python blender/products/render_match.py
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_products as bp  # noqa: E402
import render_clay as rc  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "renders", "coffee-table_rev7"))
REF_W, REF_H = 854, 1280
# Reference measurements (pixels in the photo)
REF_TOP_CENTRE = (427, 616)       # where the stone's top-surface centre projects
ELEV, AZIM = 19.0, 39.0           # degrees, solved from the stone top
LENS, SCALE_PX_PER_M = 50.0, 591.0


def look_dir(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def add_camera(loc, target, lens=None, ortho_scale=None, res=(1600, 1000), shift=(0, 0)):
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o)
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    if ortho_scale:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho_scale
    else:
        cd.lens = lens
    cd.shift_x, cd.shift_y = shift
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100


def render(name):
    path = os.path.join(OUT, name)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] rendered", path)


def main():
    os.makedirs(OUT, exist_ok=True)
    root = bp.build_one("coffee-table")
    rc.assign_clay()
    rc.cyclorama()
    rc.setup_render()
    rc.frame_camera(root, dict(az=38, el=25, lens=50, tz=0.2, res=(1600, 1000)))  # lights

    top_z = bp.coffee_top_z()
    target = Vector((0, 0, top_z))
    f_px = LENS / 36 * REF_W
    dist = f_px / SCALE_PX_PER_M
    shift = ((REF_W / 2 - REF_TOP_CENTRE[0]) / REF_W, (REF_TOP_CENTRE[1] - REF_H / 2) / REF_W)
    # shift moves the frame; positive shift_y moves content down in Blender terms
    add_camera(target + look_dir(AZIM, ELEV) * dist, target, lens=LENS,
               res=(REF_W * 2, REF_H * 2), shift=(-shift[0], shift[1]))
    render("match.png")

    # Inspection: orthographic elevations and plan with edge lines (Freestyle),
    # plus a low three-quarter view that shows the open gap and the panel.
    s = bpy.context.scene
    s.render.use_freestyle = True
    s.render.line_thickness_mode = "ABSOLUTE"
    s.render.line_thickness = 1.2
    ls = s.view_layers[0].freestyle_settings.linesets[0]
    ls.select_by_visibility = True
    ls.select_crease = True
    ls.select_silhouette = True
    ls.select_border = True
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("orden_lines")
    ls.linestyle.color = (0.08, 0.08, 0.08)
    # orthographic views: no backdrop, light seamless background, ground line
    bpy.data.objects["cyclorama"].hide_render = True
    bg = s.world.node_tree.nodes["Background"]
    old_bg = (tuple(bg.inputs["Color"].default_value), bg.inputs["Strength"].default_value)
    bg.inputs["Color"].default_value = (0.92, 0.91, 0.89, 1)
    bg.inputs["Strength"].default_value = 1.0
    s.render.film_transparent = False
    centre = Vector((-0.015, 0.0, top_z / 2))
    for name, az, el, scale in (("inspect_front", 0, 0, 1.75), ("inspect_left", 90, 0, 1.75), ("inspect_plan", 0, 89.999, 1.75)):
        add_camera(centre + look_dir(az, el) * 5, centre, ortho_scale=scale, res=(1400, 1000))
        render(f"{name}.png")
    s.render.use_freestyle = False
    bpy.data.objects["cyclorama"].hide_render = False
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = old_bg
    low_target = Vector((-0.015, 0.0, 0.14))
    add_camera(low_target + look_dir(36, 7) * 3.1, low_target, lens=50, res=(1400, 1000))
    render("inspect_low_three_quarter.png")


if __name__ == "__main__":
    main()
