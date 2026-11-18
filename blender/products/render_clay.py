"""
Phase 1 geometry validation: clay renders of each product in a neutral studio.

    blender -b --factory-startup --python blender/products/render_clay.py [-- coffee-table bedside-table wardrobe]

Components are tinted by material role (stone light, carcass mid, base dark,
accents warm) purely to make the construction readable. These are NOT the
final materials; those come in Phase 2 with the approved scanned PBR sets.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_products as bp  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "renders", "phase1_clay"))

CLAY = {
    "travertine": (0.72, 0.68, 0.60),
    "marble": (0.86, 0.86, 0.85),
    "body": (0.11, 0.075, 0.055),   # dark walnut value (clay, no texture)
    "base": (0.08, 0.075, 0.07),
    "accent": (0.48, 0.36, 0.24),
    "metal": (0.55, 0.55, 0.55),
    "interior": (0.70, 0.66, 0.58),
}

SHOTS = {
    # azimuth from the front towards the left, elevation, lens, target height, resolution
    "coffee-table": dict(az=32, el=30, lens=65, tz=0.16, res=(1600, 1200)),
    "bedside-table": dict(az=33, el=17, lens=75, tz=0.25, res=(1600, 1200)),
    "wardrobe": dict(az=24, el=6, lens=55, tz=1.03, res=(1200, 1600)),
}


def clay_material(role):
    m = bpy.data.materials.new(f"clay_{role}")
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*CLAY[role], 1)
    bsdf.inputs["Roughness"].default_value = 0.35 if role in ("marble", "metal") else 0.6
    if role == "metal":
        bsdf.inputs["Metallic"].default_value = 1.0
    return m


def assign_clay():
    mats = {r: clay_material(r) for r in CLAY}
    for o in bpy.data.objects:
        if o.type == "MESH" and "role" in o:
            o.data.materials.clear()
            o.data.materials.append(mats[o["role"]])


def cyclorama():
    """Seamless studio backdrop: floor sweeping up into a back wall."""
    bm = bmesh.new()
    prof = [(-12.0, 0.0)]
    r, cy = 1.2, 2.2
    prof.append((cy, 0.0))
    for i in range(1, 17):
        a = (math.pi / 2) * i / 16
        prof.append((cy + math.sin(a) * r, r - math.cos(a) * r))
    prof.append((cy + r, 12.0))
    width = 40
    rows = []
    for x in (-width / 2, width / 2):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new("cyc")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("cyclorama", me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("cyc")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.78, 0.76, 0.72, 1)
    b.inputs["Roughness"].default_value = 0.9
    me.materials.append(m)
    return ob


def area(name, loc, target, size, energy, color=(1, 0.97, 0.93), shape="RECTANGLE", size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def setup_render():
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type != "CPU"
    s.cycles.device = "GPU"
    s.cycles.samples = 192
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPENIMAGEDENOISE"
    s.cycles.max_bounces = 10
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.49, 0.47, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    s.world = world


def frame_camera(root, shot):
    meshes = [c for c in root.children if c.type == "MESH"]
    bpy.context.view_layer.update()
    pts = [c.matrix_world @ Vector(v) for c in meshes for v in c.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    target = Vector((centre.x, centre.y, shot["tz"]))

    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = shot["lens"]
    cam_d.sensor_width = 36
    w, h = shot["res"]
    vfov = 2 * math.atan((18 if h > w else 18 * h / w) / shot["lens"])
    dist = radius / math.sin(vfov / 2) * 1.02
    az, el = math.radians(shot["az"]), math.radians(shot["el"])
    loc = target + Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    cam = bpy.data.objects.new("cam", cam_d)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = w, h

    # lights scaled to the piece
    k = max(radius, 0.5)
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    area("key", (-2.4 * k, -2.0 * k, 2.2 * k + target.z), target, 1.8 * k, 130 * k * k)
    area("fill", (2.8 * k, -1.6 * k, 1.2 * k + target.z), target, 2.6 * k, 35 * k * k, (0.95, 0.97, 1.0))
    area("top", (0, 0.2 * k, 3.0 * k + target.z), target, 3.0 * k, 60 * k * k)
    area("rim", (1.6 * k, 2.2 * k, 1.6 * k + target.z), target, 1.4 * k, 45 * k * k)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(SHOTS)
    os.makedirs(OUT, exist_ok=True)
    for pid in argv:
        root = bp.build_one(pid)
        assign_clay()
        cyclorama()
        setup_render()
        frame_camera(root, SHOTS[pid])
        bpy.context.scene.render.filepath = os.path.join(OUT, f"{pid}.png")
        bpy.ops.render.render(write_still=True)
        print("[ORDEN] rendered", bpy.context.scene.render.filepath)


if __name__ == "__main__":
    main()
