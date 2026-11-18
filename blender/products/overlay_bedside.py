"""
Bedside table outline check against its reference photograph, using the
camera solved by fit_bedside.py (level two-point perspective, long lens,
off-centre principal point because the photo is a crop).

    blender -b --factory-startup --python blender/products/overlay_bedside.py -- <ref.jpg> <out.png>
"""
import json, math, os, sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_products as bp  # noqa: E402

W_IMG, H_IMG = 1018, 835
PALETTE = [(1, 0.1, 0.1), (0.1, 1, 0.2), (0.2, 0.5, 1), (1, 0.9, 0.1), (1, 0.2, 1), (0.1, 1, 1), (1, 0.55, 0.1), (0.6, 0.3, 1), (1, 1, 1)]


def solved_camera():
    q = json.load(open(os.path.join(HERE, "bedside_camera_fit.json")))
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    cd.lens = q["fpx"] * 36 / W_IMG
    cd.shift_x = (W_IMG / 2 - q["ppx"]) / W_IMG
    cd.shift_y = -(H_IMG / 2 - q["ppy"]) / W_IMG
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (q["cx"], q["cy"], q["cz"])
    a = math.radians(q["yaw"])
    fwd = Vector((math.sin(a), math.cos(a), 0))
    cam.rotation_euler = fwd.to_track_quat("-Z", "Y").to_euler()
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x, s.render.resolution_y = W_IMG, H_IMG


def main():
    ref_path, out_path = sys.argv[sys.argv.index("--") + 1:][:2]
    root = bp.build_one("bedside-table")
    names = sorted(c.name for c in root.children if c.type == "MESH")
    for i, o in enumerate(sorted((c for c in root.children if c.type == "MESH"), key=lambda o: o.name)):
        m = bpy.data.materials.new(f"id_{o.name}")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*PALETTE[i % len(PALETTE)], 1)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs[0])
        o.data.materials.clear()
        o.data.materials.append(m)
        o.pass_index = i + 1
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE_NEXT"
    s.view_settings.view_transform = "Standard"
    s.render.film_transparent = True
    s.world = bpy.data.worlds.new("black")
    solved_camera()
    mask_path = out_path.replace(".png", "_mask.png")
    s.render.filepath = mask_path
    s.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)

    m = np.array(bpy.data.images.load(mask_path).pixels[:], np.float32).reshape(H_IMG, W_IMG, 4)
    ref = bpy.data.images.load(ref_path)
    r = np.array(ref.pixels[:], np.float32).reshape(ref.size[1], ref.size[0], 4)
    # label by nearest palette colour
    label = np.zeros((H_IMG, W_IMG), np.int16)
    for i, col in enumerate(PALETTE[:len(names)], start=1):
        hit = (m[..., 3] > 0.5) & (np.abs(m[..., :3] - np.array(col)).sum(-1) < 0.35)
        label[hit] = i
    edge = np.zeros_like(label)
    for dy, dx in ((1, 0), (0, 1)):
        sh = np.roll(np.roll(label, dy, 0), dx, 1)
        d = sh != label
        edge[d] = np.maximum(label, sh)[d]
    for i in range(1, len(names) + 1):
        r[edge == i, :3] = PALETTE[i - 1]
    img = bpy.data.images.new("ov", W_IMG, H_IMG, alpha=True)
    img.pixels[:] = r.ravel()
    img.filepath_raw = out_path
    img.file_format = "PNG"
    img.save()
    print("[ORDEN] legend:", ", ".join(f"{n}={PALETTE[i]}" for i, n in enumerate(names)))
    print("[ORDEN] overlay", out_path)


if __name__ == "__main__":
    main()
