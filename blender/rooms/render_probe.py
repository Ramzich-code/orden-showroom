"""
Light probe per room for the real-time product: an equirectangular HDR seen
from where the product stands, rendered in Cycles with the product (and the
decor resting on it) hidden. The website uses it as the GLB's environment so
the live product is lit by the same room as the Cycles plate.

    blender -b --factory-startup --python blender/rooms/render_probe.py -- [living bedroom storage] [samples]

Output: blender/renders/final/<room>/probe.hdr (linear, 512 x 256).
Orientation: image centre = world +X (Blender) = three.js +X, which is the
three.js equirectangular convention, so no rotation is needed on the web.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room_kit as rk  # noqa: E402
import rooms  # noqa: E402
import render_final as rf  # noqa: E402


def probe(room, samples, pid=None):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, f"{room}.blend"))
    rk.preview_settings(samples=samples, res=(512, 256), exposure=0.0)
    s = bpy.context.scene
    s.use_nodes = False
    pid = pid or rf.PRODUCT[room]
    pobs = rf.product_objects(pid)
    meshes = [o for o in pobs if o.type == "MESH"]
    lo = [min(rf.world_bbox(o)[0][i] for o in meshes) for i in range(3)]
    hi = [max(rf.world_bbox(o)[1][i] for o in meshes) for i in range(3)]
    for p in rf.ROOM_PRODUCTS[room]:                  # the room without any product
        obs = rf.product_objects(p)
        for o in obs + rf.resting_on(obs):
            o.hide_render = True
    cd = bpy.data.cameras.new("probe")
    cd.type = "PANO"
    cd.panorama_type = "EQUIRECTANGULAR"
    cam = bpy.data.objects.new("probe", cd)
    s.collection.objects.link(cam)
    cam.location = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, min(0.9, (lo[2] + hi[2]) / 2 + 0.1))
    cam.rotation_euler = (math.radians(90), 0, math.radians(-90))   # forward +X, up +Z
    s.camera = cam
    s.render.image_settings.file_format = "HDR"
    out = os.path.abspath(os.path.join(rf.OUT, room, f"probe-{pid}.hdr"))
    s.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] probe", out, "at", tuple(round(v, 2) for v in cam.location))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = [a for a in args if a in rf.PRODUCT] or list(rf.PRODUCT)
    samples = next((int(a) for a in args if a.isdigit()), 128)
    for r in names:
        for p in rf.ROOM_PRODUCTS[r]:
            probe(r, samples, p)
