"""
Orthographic-style geometry review of one product: front, side (left),
three-quarter (matching the reference camera). Same neutral clay studio.

    blender -b --factory-startup --python blender/products/render_views.py -- coffee-table
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

VIEWS = {
    # name: azimuth (deg from front towards left), elevation, orthographic?, lens
    "front": (0, 0, True, None),
    "side-left": (90, 0, True, None),
    "three-quarter": (42, 27, False, 50),
}


def camera(root, az, el, ortho, lens, res=(1600, 1000)):
    bpy.context.view_layer.update()
    pts = [c.matrix_world @ Vector(v) for c in root.children if c.type == "MESH" for v in c.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o)
    cd = bpy.data.cameras.new("cam")
    a, e = math.radians(az), math.radians(el)
    direction = Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = max(hi.x - lo.x, hi.y - lo.y) * 1.25
        dist = 6
    else:
        cd.lens = lens
        vfov = 2 * math.atan(18 * res[1] / res[0] / lens)
        dist = radius / math.sin(vfov / 2) * 1.0
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = centre + direction * dist
    cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x, s.render.resolution_y = res
    return centre, radius


def main():
    pid = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "coffee-table"
    out = os.path.join(rc.OUT, "..", f"{pid}_review")
    os.makedirs(out, exist_ok=True)
    root = bp.build_one(pid)
    rc.assign_clay()
    rc.cyclorama()
    rc.setup_render()
    # light once from the three-quarter framing, keep it for all views
    rc.frame_camera(root, dict(az=35, el=30, lens=50, tz=0.15, res=(1600, 1000)))
    for name, (az, el, ortho, lens) in VIEWS.items():
        camera(root, az, el, ortho, lens)
        bpy.context.scene.render.filepath = os.path.join(out, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print("[ORDEN] rendered", os.path.abspath(bpy.context.scene.render.filepath))


if __name__ == "__main__":
    main()
