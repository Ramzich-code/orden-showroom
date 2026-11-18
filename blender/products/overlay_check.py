"""
Silhouette check: renders a flat component-ID mask of the coffee table from
the reference-matched camera and draws its outlines over the reference photo.

    blender -b --factory-startup --python blender/products/overlay_check.py -- <reference.jpg> <out.png>

Outline colours: top = red, platform = green, panel = blue.
"""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_products as bp  # noqa: E402
import render_match as rm  # noqa: E402

IDS = {"top": (1, 0, 0), "platform": (0, 1, 0), "panel": (0, 0, 1)}


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    ref_path, out_path = args[:2]
    import json
    over = json.loads(args[2]) if len(args) > 2 else {}
    for k, v in over.items():
        if hasattr(rm, k):
            setattr(rm, k, v)
        else:
            bp.COFFEE[k] = v
    print("[ORDEN] params", over)
    root = bp.build_one("coffee-table")
    for o in root.children:
        m = bpy.data.materials.new(f"id_{o.name}")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*IDS[o.name], 1)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs[0])
        o.data.materials.clear()
        o.data.materials.append(m)
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "EEVEE_NEXT") or True else "CYCLES"
    try:
        s.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        s.render.engine = "BLENDER_EEVEE"
    s.view_settings.view_transform = "Standard"
    s.render.film_transparent = True
    w = bpy.data.worlds.new("black")
    s.world = w

    top_z = bp.coffee_top_z()
    from mathutils import Vector
    target = Vector((0, 0, top_z))
    dist = (rm.LENS / 36 * rm.REF_W) / rm.SCALE_PX_PER_M
    shift = ((rm.REF_W / 2 - rm.REF_TOP_CENTRE[0]) / rm.REF_W, (rm.REF_TOP_CENTRE[1] - rm.REF_H / 2) / rm.REF_W)
    rm.add_camera(target + rm.look_dir(rm.AZIM, rm.ELEV) * dist, target, lens=rm.LENS,
                  res=(rm.REF_W, rm.REF_H), shift=(-shift[0], shift[1]))
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA"
    mask_path = out_path.replace(".png", "_mask.png")
    s.render.filepath = mask_path
    bpy.ops.render.render(write_still=True)

    mask = bpy.data.images.load(mask_path)
    W, H = mask.size
    m = np.array(mask.pixels[:], dtype=np.float32).reshape(H, W, 4)
    ref = bpy.data.images.load(ref_path)
    r = np.array(ref.pixels[:], dtype=np.float32).reshape(ref.size[1], ref.size[0], 4)
    assert (ref.size[0], ref.size[1]) == (W, H), (ref.size[:], (W, H))
    label = np.zeros((H, W), dtype=np.int8)
    for i, col in enumerate(IDS.values(), start=1):
        hit = (m[..., 3] > 0.5) & (np.abs(m[..., :3] - np.array(col)).sum(-1) < 0.6)
        label[hit] = i
    edge = np.zeros((H, W), dtype=np.int8)
    for dy, dx in ((1, 0), (0, 1), (1, 1), (-1, 1)):
        sh = np.roll(np.roll(label, dy, 0), dx, 1)
        diff = (sh != label)
        edge[diff & (label > 0)] = label[diff & (label > 0)]
    colours = {1: (1, 0.1, 0.1), 2: (0.1, 1, 0.2), 3: (0.2, 0.5, 1)}
    for i, col in colours.items():
        r[edge == i, :3] = col
    out = bpy.data.images.new("overlay", W, H, alpha=True)
    out.pixels[:] = r.ravel()
    out.filepath_raw = out_path
    out.file_format = "PNG"
    out.save()
    print("[ORDEN] overlay", out_path)


if __name__ == "__main__":
    main()
