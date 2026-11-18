"""
Geometry review of the Lys headboard shelf: a wall-mounted ledge 1.17 m up,
too long and thin for the generic views. Clay studio, LEDs lit.

    blender -b --factory-startup --python blender/products/render_headboard_shelf.py

Output: blender/renders/headboard-shelf_review/{overall,detail,section}.png
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

OUT = os.path.abspath(os.path.join(rc.OUT, "..", "headboard-shelf_review"))


def shot(name, target, az, el, dist, lens, res=(1600, 1000)):
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    a, e = math.radians(az), math.radians(el)
    d = Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector(target) + d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x, s.render.resolution_y = res
    s.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] rendered", s.render.filepath)


def main():
    os.makedirs(OUT, exist_ok=True)
    root = bp.build_one("headboard-shelf")
    rc.assign_clay()
    light = bpy.data.materials.get("clay_light")
    bsdf = light.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.78, 0.45, 1)
    bsdf.inputs["Emission Strength"].default_value = 6.0
    rc.cyclorama()
    rc.setup_render()
    z = bp.HEADBOARD_SHELF["z"]
    rc.frame_camera(root, dict(az=30, el=35, lens=50, tz=z, res=(1600, 1000)))   # studio lights at shelf height
    shot("overall", (0, 0, z), 28, 38, 2.9, 40)
    shot("detail", (0.62, 0.0, z), 34, 42, 0.95, 50)
    shot("section", (-1.1, 0.0, z - 0.06), 90, 8, 0.75, 50)


if __name__ == "__main__":
    main()
