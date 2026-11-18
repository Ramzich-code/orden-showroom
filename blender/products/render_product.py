"""
Phase 2: individual photoreal product renders (Cycles, studio HDRI).

    blender -b --factory-startup --python blender/products/render_product.py -- <product> <finish> [samples] [view]

finish: signature | white | black | oak       view: hero (default) | front | close
Output: blender/renders/phase2/<product>_<finish>_<view>.png
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_products as bp  # noqa: E402
import materials as mats  # noqa: E402
import render_clay as rc  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "renders", "phase2"))
HDRI = os.path.join(mats.ASSETS, "studio_small_09", "studio_small_09_4k.hdr")

VIEWS = {
    # azimuth from front towards left, elevation, lens, target height, distance factor
    "coffee-table": {"hero": (36, 21, 70, 0.17, 1.0), "front": (6, 8, 85, 0.15, 1.05), "close": (52, 26, 100, 0.22, 0.55)},
    "bedside-table": {"hero": (33, 17, 75, 0.25, 1.0), "front": (5, 6, 85, 0.25, 1.05), "close": (40, 30, 100, 0.40, 0.55)},
    "wardrobe": {"hero": (26, 6, 55, 1.03, 1.0), "front": (4, 3, 70, 1.03, 1.05), "close": (35, 10, 85, 1.05, 0.5)},
}


def studio_world(strength=1.0, rotation_deg=200):
    w = bpy.data.worlds.new("studio_hdri")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(HDRI, check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rotation_deg))
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    bpy.context.scene.world = w


def backdrop():
    cyc = rc.cyclorama()
    m = cyc.data.materials[0]
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.50, 0.47, 0.43, 1)   # warm stone-grey sweep
    b.inputs["Roughness"].default_value = 0.85
    return cyc


def camera_for(root, view):
    az, el, lens, tz, k = view
    bpy.context.view_layer.update()
    pts = [c.matrix_world @ Vector(v) for c in root.children if c.type == "MESH" for v in c.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    target = Vector((centre.x, centre.y, tz))
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_width = 36
    s = bpy.context.scene
    w, h = s.render.resolution_x, s.render.resolution_y
    vfov = 2 * math.atan(18 * min(w, h) / max(w, h) / lens)
    dist = radius / math.sin(vfov / 2) * 1.02 * k
    a, e = math.radians(az), math.radians(el)
    d = Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam = bpy.data.objects.new("cam", cd)
    s.collection.objects.link(cam)
    cam.location = target + d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cd.dof.use_dof = view is not None and k < 0.8
    cd.dof.focus_distance = dist
    cd.dof.aperture_fstop = 5.6
    s.camera = cam
    return target, radius


def key_light(target, radius):
    ld = bpy.data.lights.new("key", "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = 2.4 * max(radius, 0.6), 1.6 * max(radius, 0.6)
    ld.energy = 260 * max(radius, 0.6) ** 2
    ld.color = (1.0, 0.96, 0.9)
    ob = bpy.data.objects.new("key", ld)
    bpy.context.scene.collection.objects.link(ob)
    k = max(radius, 0.6)
    ob.location = target + Vector((-2.6 * k, -1.2 * k, 2.4 * k))
    ob.rotation_euler = (target - ob.location).to_track_quat("-Z", "Y").to_euler()


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    pid = args[0] if args else "coffee-table"
    finish = args[1] if len(args) > 1 else "signature"
    samples = int(args[2]) if len(args) > 2 else 512
    view = args[3] if len(args) > 3 else "hero"

    root = bp.build_one(pid)
    mats.apply_finish(root, pid, finish)
    backdrop()
    rc.setup_render()
    s = bpy.context.scene
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.006
    s.cycles.max_bounces = 12
    s.cycles.glossy_bounces = 6
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.0
    s.render.resolution_x, s.render.resolution_y = (2400, 1600) if pid != "wardrobe" else (1600, 2200)
    studio_world(strength=0.9)
    target, radius = camera_for(root, VIEWS[pid][view])
    key_light(target, radius)

    os.makedirs(OUT, exist_ok=True)
    s.render.filepath = os.path.join(OUT, f"{pid}_{finish}_{view}.png")
    bpy.ops.render.render(write_still=True)
    print("[ORDEN] rendered", s.render.filepath)


if __name__ == "__main__":
    main()
