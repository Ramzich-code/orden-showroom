"""
ORDEN phase 3: final Cycles stills of the approved rooms (no animation).

    blender -b --factory-startup --python blender/rooms/render_final.py -- [living bedroom storage] [samples] [WxH] [portrait]

"portrait" renders only the 9:16 phone cameras (cam_*_p, see portrait.py) at
1080 x 1920 and merges them into the existing <room>.json.

For each room (loaded from blender/rooms/<room>.blend) and each camera:
  <cam>_beauty.png  full render, product in place (default room view)
  <cam>_plate.png   same view WITHOUT the product and what rests on it; the
                    website lays the real-time GLB over this plate
  <cam>_depth.png   16-bit mist/depth (white = near) for the subtle parallax
and one <room>.json with each camera in three.js coordinates (Y-up), its
vertical fov and the product position, so the GLB lines up with the plate.
Output: blender/renders/final/<room>/
"""
import json
import math
import os
import shutil
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room_kit as rk  # noqa: E402
import rooms  # noqa: E402

OUT = os.path.join(HERE, "..", "renders", "final")
PRODUCT = {"living": "coffee-table", "bedroom": "bedside-table", "storage": "wardrobe"}
Z_UP_TO_Y_UP = Matrix.Rotation(-math.pi / 2, 4, "X")
MIST_START, MIST_DEPTH = 0.3, 9.0


def world_bbox(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def product_objects(pid):
    col = bpy.data.collections[pid]
    return [o for o in col.all_objects]


def resting_on(pobs):
    """Decor standing on the product (vase, books, styling): above the floor,
    its centre inside the product footprint, its base at or below the top."""
    meshes = [o for o in pobs if o.type == "MESH"]
    lo = Vector((min(world_bbox(o)[0].x for o in meshes), min(world_bbox(o)[0].y for o in meshes), 0))
    hi = Vector((max(world_bbox(o)[1].x for o in meshes), max(world_bbox(o)[1].y for o in meshes),
                 max(world_bbox(o)[1].z for o in meshes)))
    found = []
    for o in bpy.data.objects:
        if o in pobs or o.type != "MESH" or o.hide_render:
            continue
        a, b = world_bbox(o)
        c = (a + b) / 2
        if (a.z > 0.05 and a.z <= hi.z + 0.30          # stems start inside the vase
                and lo.x - 0.02 <= c.x <= hi.x + 0.02 and lo.y - 0.02 <= c.y <= hi.y + 0.02):
            found.append(o)
    # small loose pieces touching what was found (leaves on the branches...)
    boxes = {o: world_bbox(o) for o in bpy.data.objects if o.type == "MESH" and o not in pobs}
    grow = True
    while grow:
        grow = False
        for o, (a, b) in boxes.items():
            if o in found or max(b - a) > 0.12 or a.z <= 0.05:
                continue
            for f in found:
                fa, fb = boxes[f]
                if all(a[i] <= fb[i] + 0.01 and b[i] >= fa[i] - 0.01 for i in range(3)):
                    found.append(o)
                    grow = True
                    break
    # take each item's whole group (stems, second book, sphere in the bowl...)
    roots = set()
    for o in found:
        while o.parent is not None:
            o = o.parent
        roots.add(o)
    out = []
    for r in roots:
        out += [r] + list(r.children_recursive)
    return out


def setup_depth(room_dir):
    s = bpy.context.scene
    bpy.context.view_layer.use_pass_mist = True
    ms = s.world.mist_settings
    ms.start, ms.depth, ms.falloff = MIST_START, MIST_DEPTH, "LINEAR"
    s.use_nodes = True
    nt = s.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], comp.inputs["Image"])
    inv = nt.nodes.new("CompositorNodeInvert")          # white = near
    nt.links.new(rl.outputs["Mist"], inv.inputs["Color"])
    fo = nt.nodes.new("CompositorNodeOutputFile")
    fo.base_path = room_dir
    fo.format.file_format = "PNG"
    fo.format.color_mode = "BW"
    fo.format.color_depth = "16"
    fo.file_slots[0].path = "depth_"
    nt.links.new(inv.outputs["Color"], fo.inputs[0])
    return fo


def three_camera(cam, aspect):
    m = Z_UP_TO_Y_UP @ cam.matrix_world
    q = m.to_quaternion()
    # sensor fit AUTO: the sensor width spans the longer side of the frame
    half = math.atan(cam.data.sensor_width / 2 / cam.data.lens)
    vfov = 2 * math.atan(math.tan(half) / aspect) if aspect >= 1 else 2 * half
    return dict(position=[round(v, 5) for v in m.translation],
                quaternion=[round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6)],
                fov=round(math.degrees(vfov), 4), lens_mm=cam.data.lens)


def render_room(room, samples, res, portrait=False):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, f"{room}.blend"))
    rk.preview_settings(samples=samples, res=res, exposure=rooms.EXPOSURE[room])
    s = bpy.context.scene
    room_dir = os.path.abspath(os.path.join(OUT, room))
    os.makedirs(room_dir, exist_ok=True)
    fo = setup_depth(room_dir)
    pid = PRODUCT[room]
    pobs = product_objects(pid)
    decor = resting_on(pobs)
    print("[ORDEN] hidden on plate:", [o.name for o in decor])
    root = next(o for o in pobs if o.parent is None)
    json_path = os.path.join(room_dir, f"{room}.json")
    previous = json.load(open(json_path)) if portrait and os.path.exists(json_path) else None
    info = dict(room=room, product=pid, resolution=list(res),
                product_position=[round(v, 5) for v in (Z_UP_TO_Y_UP @ root.matrix_world).translation],
                product_rotation_y=round(root.rotation_euler.z, 6),
                depth=dict(near=MIST_START, far=MIST_START + MIST_DEPTH, encoding="white=near, linear"),
                cameras={})
    cams = [o for o in bpy.data.objects if o.type == "CAMERA" and o.name.startswith("cam_")
            and o.name.endswith("_p") == portrait]
    if previous:
        info["cameras"] = previous["cameras"]
        info["resolution"] = previous["resolution"]
        info["resolution_portrait"] = list(res)
    for cam in sorted(cams, key=lambda c: c.name, reverse=True):     # cam_room first
        s.camera = cam
        info["cameras"][cam.name] = three_camera(cam, res[0] / res[1])
        # beauty + depth
        fo.mute = False
        s.render.filepath = os.path.join(room_dir, f"{cam.name}_beauty.png")
        bpy.ops.render.render(write_still=True)
        tmp = os.path.join(room_dir, f"depth_{s.frame_current:04d}.png")
        shutil.move(tmp, os.path.join(room_dir, f"{cam.name}_depth.png"))
        print("[ORDEN] rendered", s.render.filepath)
        # plate without the product
        fo.mute = True
        for o in pobs + decor:
            o.hide_render = True
        s.render.filepath = os.path.join(room_dir, f"{cam.name}_plate.png")
        bpy.ops.render.render(write_still=True)
        for o in pobs + decor:
            o.hide_render = False
        print("[ORDEN] rendered", s.render.filepath)
    with open(json_path, "w") as f:
        json.dump(info, f, indent=2)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = [a for a in args if a in PRODUCT] or list(PRODUCT)
    samples = next((int(a) for a in args if a.isdigit()), 512)
    portrait = "portrait" in args
    res = next((tuple(int(v) for v in a.split("x")) for a in args if "x" in a and a[0].isdigit()),
               (1080, 1920) if portrait else (2560, 1440))
    for room in names:
        render_room(room, samples, res, portrait)


if __name__ == "__main__":
    main()
