"""
Sofa vs. the client's reference photo: clay sofa rendered from roughly the
photo's viewpoint (front, slightly from the left, eye just above the back),
in boucle-cream clay, for a side-by-side check.

    blender -b --factory-startup --python blender/products/render_sofa_match.py

Output: blender/renders/sofa_review/photo_angle.png
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

OUT = os.path.abspath(os.path.join(rc.OUT, "..", "sofa_review"))


def main():
    os.makedirs(OUT, exist_ok=True)
    root = bp.build_one("sofa")
    rc.assign_clay()
    fab = bpy.data.materials.get("clay_fabric")
    if fab:
        b = fab.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.62, 0.55, 0.45, 1)
        b.inputs["Roughness"].default_value = 0.9
        b.inputs["Sheen Weight"].default_value = 0.6
    rc.cyclorama()
    rc.setup_render()
    rc.frame_camera(root, dict(az=8, el=8, lens=50, tz=0.4, res=(1536, 576)))
    # photo-like camera: low, frontal, slight left yaw, wide aspect
    cam = bpy.context.scene.camera
    target = Vector((0.15, 0, 0.42))
    loc = Vector((-0.55, -3.6, 0.82))
    cam.location = loc
    cam.data.lens = 42
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = 1536, 576
    s.render.filepath = os.path.join(OUT, "photo_angle.png")
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] rendered", s.render.filepath)


if __name__ == "__main__":
    main()
