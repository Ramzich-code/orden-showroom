"""
ORDEN room kit: shared building blocks for the three independent room scenes.

  * room shell with a real window opening, plaster walls, oak floor, skirting
  * daylight: sun lamp through the window + garden HDRI for sky / exterior view
  * soft upholstered volumes (bevel + subdivision) for sofas, beds, headboards
  * imported CC0 decor (plant, vase) and the approved ORDEN products, built
    from blender/products/build_products.py (same code = same geometry)

Conventions: metres, Z up, the room's main view looks towards +Y (back wall at
+D/2); products face -Y as in their own files.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCTS = os.path.abspath(os.path.join(HERE, "..", "products"))
sys.path.insert(0, PRODUCTS)
import build_products as bp  # noqa: E402
import materials as mats  # noqa: E402

ASSETS = mats.ASSETS
RENDERS = os.path.abspath(os.path.join(HERE, "..", "renders", "rooms_preview"))


# --------------------------------------------------------------------------- scene

def new_scene():
    bp.reset_scene()
    mats._cache.clear()   # materials are deleted with the old scene
    col = bpy.data.collections.new("room")
    bpy.context.scene.collection.children.link(col)
    return col


def _obj(name, bm, loc, mat_key, col, grain="x", smooth_angle=35):
    bp.box_uv(bm, grain)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    except AttributeError:
        pass
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.location = loc
    if mat_key:
        me.materials.append(mats.material(mat_key))
    return ob


def hard_box(name, size, loc, mat_key, col, edge=0.002, grain="x"):
    return _obj(name, bp.panel_bmesh(size, edge, 2), loc, mat_key, col, grain)


def soft_box(name, size, loc, mat_key, col, roundness=0.04, level=2, rot=None):
    """Upholstered volume: chamfered box smoothed by subdivision."""
    bm = bp._box_bmesh(*size)
    bp._bevel(bm, list(bm.edges), roundness, 2)
    ob = _obj(name, bm, loc, mat_key, col, smooth_angle=180)
    if rot:
        ob.rotation_euler = rot
    sub = ob.modifiers.new("soft", "SUBSURF")
    sub.levels = sub.render_levels = level
    return ob


def cylinder(name, r1, r2, h, loc, mat_key, col, segments=48):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r1, radius2=r2, depth=h)
    return _obj(name, bm, loc, mat_key, col, grain="z")


# --------------------------------------------------------------------------- shell

def shell(col, W, D, H=2.8, window=None, wall_t=0.15, wall="plaster", floor="floor", skirting=True):
    """Closed room: floor, ceiling, four walls; optional window opening in the
    left (-X) or right (+X) wall: window = dict(side, y0, y1, z0, z1)."""
    x0, x1, y0, y1 = -W / 2, W / 2, -D / 2, D / 2
    hard_box("room_floor", (W, D, 0.02), (0, 0, -0.01), floor, col)
    hard_box("room_ceiling", (W + 2 * wall_t, D + 2 * wall_t, 0.1), (0, 0, H + 0.05), "white", col)
    hard_box("room_wall_back", (W + 2 * wall_t, wall_t, H), (0, y1 + wall_t / 2, H / 2), wall, col)
    hard_box("room_wall_front", (W + 2 * wall_t, wall_t, H), (0, y0 - wall_t / 2, H / 2), wall, col)
    for side, x in (("left", x0 - wall_t / 2), ("right", x1 + wall_t / 2)):
        if window and window["side"] == side:
            wy0, wy1, wz0, wz1 = window["y0"], window["y1"], window["z0"], window["z1"]
            blocks = [((y0, y1), (0, wz0)), ((y0, y1), (wz1, H)), ((y0, wy0), (wz0, wz1)), ((wy1, y1), (wz0, wz1))]
            for i, ((ya, yb), (za, zb)) in enumerate(blocks):
                if yb - ya > 1e-3 and zb - za > 1e-3:
                    hard_box(f"room_wall_{side}_{i}", (wall_t, yb - ya, zb - za), (x, (ya + yb) / 2, (za + zb) / 2), wall, col)
            _window_frame(col, x, window)
        else:
            hard_box(f"room_wall_{side}", (wall_t, D, H), (x, 0, H / 2), wall, col)
    if not skirting:
        return
    # skirting
    hard_box("room_skirting_back", (W, 0.015, 0.08), (0, y1 - 0.0075, 0.04), "white", col)
    for side, x in (("left", x0 + 0.0075), ("right", x1 - 0.0075)):
        hard_box(f"room_skirting_{side}", (0.015, D, 0.08), (x, 0, 0.04), "white", col)


def _window_frame(col, x, w):
    """Slim painted frame with one mullion; no glass (clear daylight)."""
    y0, y1, z0, z1, t = w["y0"], w["y1"], w["z0"], w["z1"], 0.05
    ym = (y0 + y1) / 2
    parts = [((t, y1 - y0, t), (x, ym, z0 + t / 2)), ((t, y1 - y0, t), (x, ym, z1 - t / 2)),
             ((t, t, z1 - z0), (x, y0 + t / 2, (z0 + z1) / 2)), ((t, t, z1 - z0), (x, y1 - t / 2, (z0 + z1) / 2)),
             ((t * 0.8, t * 0.8, z1 - z0), (x, ym, (z0 + z1) / 2))]
    for i, (size, loc) in enumerate(parts):
        hard_box(f"room_window_frame_{i}", size, loc, "white", col)
    sill_x = x + (0.1 if w["side"] == "left" else -0.1)
    hard_box("room_window_sill", (0.22, y1 - y0 + 0.08, 0.025), (sill_x, ym, z0 - 0.0125), "white", col)


# --------------------------------------------------------------------------- light

def daylight(sun_rot_deg=(48, 0, -70), sun_strength=4.0, hdri_strength=1.0, hdri_rot=0):
    w = bpy.data.worlds.new("daylight")
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(ASSETS, "symmetrical_garden_02", "symmetrical_garden_02_4k.hdr"), check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(hdri_rot))
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    bg = nt.nodes["Background"]
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = hdri_strength
    bpy.context.scene.world = w
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = sun_strength
    sun.angle = math.radians(1.2)
    sun.color = (1.0, 0.93, 0.84)
    ob = bpy.data.objects.new("sun", sun)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = tuple(math.radians(a) for a in sun_rot_deg)
    return ob


def _area(name, size, loc, direction, energy, color):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size
    ld.energy = energy
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
    return ob


def window_fill(W, window, energy=900.0):
    """Soft skylight entering through the window opening: a large area light
    filling the opening, facing into the room (natural, soft, no hard shadow)."""
    side = 1 if window["side"] == "right" else -1
    x = side * (W / 2 - 0.05)
    y = (window["y0"] + window["y1"]) / 2
    z = (window["z0"] + window["z1"]) / 2
    size = (window["y1"] - window["y0"], window["z1"] - window["z0"])
    ob = _area("window_fill", size, (x, y, z), (-side, 0, 0), energy, (0.96, 0.97, 1.0))
    ob.rotation_euler.rotate_axis("Z", math.radians(90))   # long side along the wall
    return ob


def ceiling_bounce(W, D, H, energy=120.0):
    """Very soft fill standing in for light bounced off the ceiling: lifts the
    dark corners without adding visible shadows."""
    return _area("ceiling_bounce", (W * 0.8, D * 0.8), (0, 0, H - 0.05), (0, 0, -1), energy, (1.0, 0.97, 0.92))


def warm_lamp(name, loc, energy=25, radius=0.08, color=(1.0, 0.78, 0.55)):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.shadow_soft_size = radius
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


# --------------------------------------------------------------------------- products & decor

def place_product(pid, loc, rot_z=0.0, finish="signature"):
    col = bpy.data.collections.new(pid)
    bpy.context.scene.collection.children.link(col)
    root = bp.BUILDERS[pid](col)
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    mats.apply_finish(root, pid, finish)
    return root


def import_gltf(rel_path, loc, scale=1.0, rot_z=0.0, name="decor"):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, rel_path))
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc
    root.scale = (scale, scale, scale)
    root.rotation_euler = (0, 0, rot_z)
    return root, new


def stoneware(objs, colour=(0.075, 0.068, 0.060)):
    """Replace the imported classical urn by a simple cylindrical pot in matte
    charcoal stoneware of the same size (leaves untouched)."""
    m = bpy.data.materials.new("orden_stoneware")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Roughness"].default_value = 0.85
    bpy.context.view_layer.update()
    for o in objs:
        if o.type != "MESH" or not any(s.material and s.material.name.lower().endswith("_pot") for s in o.material_slots):
            continue
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        o.hide_render = o.hide_viewport = True
        r = max(hi.x - lo.x, hi.y - lo.y) / 2 * 0.9
        h = hi.z - lo.z
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=r * 0.86, radius2=r, depth=h)
        bp._bevel(bm, [e for e in bm.edges if len(e.link_faces) == 2 and abs(abs(e.verts[0].co.z) - h / 2) < 1e-5 and abs(abs(e.verts[1].co.z) - h / 2) < 1e-5], 0.01, 3)
        pot = _obj(f"{o.name}_stoneware", bm, ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + h / 2), None, bpy.context.scene.collection)
        pot.data.materials.append(m)


# --------------------------------------------------------------------------- props

def sofa(col, loc, width=2.5, depth=1.0, rot_z=0.0):
    """Contemporary low sofa: deep seat, soft rounded cushions, cream boucle."""
    root = bpy.data.objects.new("prop_sofa", None)
    col.objects.link(root)
    arm = 0.24
    seat_w = (width - 2 * arm) / 2
    parts = [
        soft_box("prop_sofa_base", (width, depth, 0.30), (0, 0, 0.19), "boucle", col, 0.06),
        soft_box("prop_sofa_seat_l", (seat_w - 0.01, depth - 0.24, 0.16), (-seat_w / 2, 0.08 - 0.12 + 0.12 - 0.08, 0.41), "boucle", col, 0.06),
        soft_box("prop_sofa_seat_r", (seat_w - 0.01, depth - 0.24, 0.16), (seat_w / 2, 0, 0.41), "boucle", col, 0.06),
        soft_box("prop_sofa_back", (width - 2 * arm + 0.02, 0.26, 0.44), (0, depth / 2 - 0.15, 0.55), "boucle", col, 0.09),
        soft_box("prop_sofa_arm_l", (arm, depth, 0.56), (-width / 2 + arm / 2, 0, 0.32), "boucle", col, 0.09),
        soft_box("prop_sofa_arm_r", (arm, depth, 0.56), (width / 2 - arm / 2, 0, 0.32), "boucle", col, 0.09),
        hard_box("prop_sofa_plinth", (width - 0.2, depth - 0.2, 0.04), (0, 0, 0.02), "base", col),
    ]
    parts[1].location.x = -seat_w / 2
    parts[1].location.y = 0
    for p in parts:
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def rug(col, size, loc):
    return hard_box("prop_rug", (size[0], size[1], 0.012), (loc[0], loc[1], 0.006), "carpet", col, 0.004)


def floor_lamp(col, loc):
    root = bpy.data.objects.new("prop_floor_lamp", None)
    col.objects.link(root)
    for p in (cylinder("prop_lamp_base", 0.16, 0.16, 0.025, (0, 0, 0.0125), "black", col),
              cylinder("prop_lamp_pole", 0.012, 0.012, 1.45, (0, 0, 0.75), "black", col),
              cylinder("prop_lamp_shade", 0.21, 0.24, 0.34, (0, 0, 1.55), "linen", col)):
        p.parent = root
    root.location = loc
    warm_lamp("prop_lamp_light", (loc[0], loc[1], 1.5), energy=18)
    return root


def books(col, loc, rot_z=0.15):
    root = bpy.data.objects.new("prop_books", None)
    col.objects.link(root)
    a = hard_box("prop_book_a", (0.30, 0.23, 0.035), (0, 0, 0.0175), "white", col, 0.003)
    b = hard_box("prop_book_b", (0.26, 0.20, 0.03), (0.01, 0.005, 0.05), "black", col, 0.003)
    for p in (a, b):
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def bed(col, loc, width=1.8, length=2.1):
    """Contemporary bed: upholstered base, tall refined headboard, linen bedding."""
    root = bpy.data.objects.new("prop_bed", None)
    col.objects.link(root)
    hb_t = 0.12
    y_head = length / 2 - hb_t / 2
    body = length - hb_t
    foot = -length / 2
    parts = [
        soft_box("prop_bed_base", (width + 0.06, body, 0.30), (0, -hb_t / 2, 0.17), "linen_sand", col, 0.03),
        hard_box("prop_bed_plinth", (width - 0.2, length - 0.4, 0.03), (0, 0, 0.015), "base", col),
        soft_box("prop_bed_headboard", (width + 0.30, hb_t, 1.12), (0, y_head, 0.56), "linen_sand", col, 0.05),
        soft_box("prop_bed_mattress", (width - 0.04, body - 0.06, 0.20), (0, -hb_t / 2, 0.42), "linen", col, 0.05),
        # duvet draped over the mattress sides, then folded back near the pillows
        soft_box("prop_bed_duvet", (width + 0.16, body * 0.80, 0.27), (0, foot + body * 0.40 - 0.03, 0.465), "linen", col, 0.09),
        soft_box("prop_bed_duvet_fold", (width + 0.16, 0.32, 0.08), (0, foot + body * 0.80 - 0.18, 0.61), "linen", col, 0.035),
        soft_box("prop_bed_throw", (width + 0.22, 0.55, 0.05), (0, foot + 0.36, 0.62), "linen_sand", col, 0.02),
        soft_box("prop_bed_pillow_l", (0.78, 0.50, 0.22), (-width / 4 - 0.02, y_head - 0.30, 0.68), "linen", col, 0.10, rot=(math.radians(-22), 0, 0)),
        soft_box("prop_bed_pillow_r", (0.78, 0.50, 0.22), (width / 4 + 0.02, y_head - 0.30, 0.68), "linen", col, 0.10, rot=(math.radians(-22), 0, 0)),
        soft_box("prop_bed_cushion", (0.55, 0.16, 0.34), (0, y_head - 0.48, 0.70), "linen_sand", col, 0.07, rot=(math.radians(-12), 0, 0)),
    ]
    for p in parts:
        p.parent = root
    root.location = loc
    return root


def table_lamp(col, loc):
    root = bpy.data.objects.new("prop_table_lamp", None)
    col.objects.link(root)
    for p in (cylinder("prop_tlamp_base", 0.075, 0.06, 0.30, (0, 0, 0.15), "travertine", col),
              cylinder("prop_tlamp_shade", 0.16, 0.18, 0.22, (0, 0, 0.42), "linen", col)):
        p.parent = root
    root.location = loc
    warm_lamp("prop_tlamp_light", (loc[0], loc[1], loc[2] + 0.38), energy=14)
    return root


def bench(col, loc, length=1.2, rot_z=0.0):
    root = bpy.data.objects.new("prop_bench", None)
    col.objects.link(root)
    parts = [soft_box("prop_bench_seat", (length, 0.40, 0.12), (0, 0, 0.40), "boucle", col, 0.04)]
    for sx in (-1, 1):
        parts.append(hard_box(f"prop_bench_leg_{sx}", (0.05, 0.36, 0.34), (sx * (length / 2 - 0.08), 0, 0.17), "oak", col, 0.004, grain="z"))
    for p in parts:
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def floor_mirror(col, loc, rot_z=0.0, w=0.70, h=1.80):
    root = bpy.data.objects.new("prop_mirror", None)
    col.objects.link(root)
    frame = hard_box("prop_mirror_frame", (w, 0.03, h), (0, 0, h / 2), "oak", col, 0.004, grain="z")
    m = bpy.data.materials.new("orden_mirror")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.02
    glass = bp._box_bmesh(w - 0.06, 0.004, h - 0.06)
    g = _obj("prop_mirror_glass", glass, (0, -0.016, h / 2), None, col)
    g.data.materials.append(m)
    for p in (frame, g):
        p.parent = root
    root.location = loc
    root.rotation_euler = (math.radians(-6), 0, rot_z)   # leaning against the wall
    return root


# --------------------------------------------------------------------------- render

def camera(name, loc, target, lens=35):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def preview_settings(samples=96, res=(1600, 900), exposure=1.6):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type != "CPU"
    s.cycles.device = "GPU"
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPENIMAGEDENOISE"
    s.cycles.max_bounces = 12
    s.cycles.diffuse_bounces = 6
    s.cycles.caustics_reflective = s.cycles.caustics_refractive = False
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Base Contrast"   # softer, more natural interior contrast
    s.view_settings.exposure = exposure
    s.render.resolution_x, s.render.resolution_y = res
    s.render.image_settings.file_format = "PNG"


def render_cameras(room, cams):
    os.makedirs(RENDERS, exist_ok=True)
    s = bpy.context.scene
    for cam in cams:
        s.camera = cam
        s.render.filepath = os.path.join(RENDERS, f"{room}_{cam.name}.png")
        bpy.ops.render.render(write_still=True)
        print("[ORDEN] rendered", s.render.filepath)
