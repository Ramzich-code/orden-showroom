"""
Props for the three ORDEN rooms, after the client's reference images.
Simple modelled geometry dressed with the scanned material library; nothing
here is an ORDEN product.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import room_kit as rk
from room_kit import _obj, bp, cylinder, hard_box, soft_box

_colour_cache = {}


def colour(name, srgb, rough=0.6, sheen=0.0, metallic=0.0, coat=0.0):
    """Plain physically based colour material (small accents)."""
    m = _colour_cache.get(name)
    try:
        if m is not None and m.name in bpy.data.materials:
            return m
    except ReferenceError:   # deleted with a previous scene
        pass
    m = bpy.data.materials.new(f"orden_{name}")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rk.mats._lin(srgb), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Coat Weight"].default_value = coat
    nt = m.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 300 if sheen > 0 else 120
    noise.inputs["Detail"].default_value = 8
    rmap = nt.nodes.new("ShaderNodeMapRange")
    rmap.inputs["To Min"].default_value = max(0.0, rough - 0.08)
    rmap.inputs["To Max"].default_value = min(1.0, rough + 0.08)
    nt.links.new(noise.outputs["Fac"], rmap.inputs["Value"])
    nt.links.new(rmap.outputs["Result"], b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12 if sheen > 0 else 0.05
    bump.inputs["Distance"].default_value = 0.0005
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    _colour_cache[name] = m
    return m


def emissive(name, srgb=(1.0, 0.78, 0.52), strength=8.0):
    m = bpy.data.materials.new(f"orden_light_{name}")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rk.mats._lin(srgb), 1)
    em.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def _set(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def group(name, col, parts, loc=(0, 0, 0), rot_z=0.0):
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    for p in parts:
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def _sphere(name, r, loc, col, mat=None, scale=(1, 1, 1), ico=False):
    bm = bmesh.new()
    if ico:
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    else:
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    ob = _obj(name, bm, loc, None, col, smooth_angle=180)
    ob.scale = scale
    if mat is not None:
        ob.data.materials.append(mat if not isinstance(mat, str) else rk.mats.material(mat))
    return ob


# ======================================================================= bedroom

def channel_headboard(col, x0, x1, y_wall, height=1.15, depth=0.12, channel=0.21, mat="linen_sand"):
    """Wide upholstered headboard with vertical channels, against the wall."""
    n = max(1, round((x1 - x0) / channel))
    w = (x1 - x0) / n
    parts = [hard_box("prop_hb_back", (x1 - x0, 0.03, height), ((x0 + x1) / 2, y_wall - 0.015, height / 2 + 0.02), "base", col)]
    for i in range(n):
        parts.append(soft_box(f"prop_hb_ch_{i}", (w - 0.006, depth, height), (x0 + w * (i + 0.5), y_wall - 0.03 - depth / 2, height / 2 + 0.02), mat, col, 0.045))
    return group("prop_headboard", col, parts)


def led_cove(col, x0, x1, y_wall, z, strength=12.0):
    """Warm indirect LED line on top of the headboard (washes the wall)."""
    ob = hard_box("prop_led_cove", (x1 - x0, 0.02, 0.012), ((x0 + x1) / 2, y_wall - 0.06, z), None, col)
    return _set(ob, emissive("cove", strength=strength))


def pendant(col, x, y, z_bottom, ceiling=2.7):
    shade_h = 0.30
    ink = colour("ink", (0.05, 0.05, 0.05), 0.45, metallic=0.5)
    cord = _set(cylinder("prop_pendant_cord", 0.003, 0.003, ceiling - z_bottom - shade_h, (x, y, (ceiling + z_bottom + shade_h) / 2), None, col, 8), ink)
    ring = _set(cylinder("prop_pendant_ring", 0.075, 0.075, 0.02, (x, y, z_bottom + shade_h + 0.01), None, col), ink)
    shade = _set(cylinder("prop_pendant_shade", 0.068, 0.068, shade_h, (x, y, z_bottom + shade_h / 2), None, col), emissive("opal", (1.0, 0.86, 0.66), 6.0))
    rk.warm_lamp("prop_pendant_light", (x, y, z_bottom - 0.05), energy=22, radius=0.07)
    return group("prop_pendant", col, [cord, ring, shade])


def art_frame(col, cx, cz, w, h, y_wall, mat="linen_sand"):
    frame = _set(hard_box("prop_art_frame", (w, 0.035, h), (cx, y_wall - 0.02, cz), None, col, 0.002), colour("ink", (0.05, 0.05, 0.05), 0.45))
    canvas = hard_box("prop_art_canvas", (w - 0.04, 0.01, h - 0.04), (cx, y_wall - 0.04, cz), mat, col, 0.001)
    return group("prop_art", col, [frame, canvas])


def sheer_curtain(col, x, y0, y1, height, folds=14, depth=0.06):
    """Floor-to-ceiling sheer: a pleated translucent sheet along a window wall."""
    bm = bmesh.new()
    nx, nz = folds * 8, 2
    rows = []
    for iz in range(nz + 1):
        row = []
        for ix in range(nx + 1):
            t = ix / nx
            row.append(bm.verts.new((x + math.sin(t * folds * 2 * math.pi) * depth / 2, y0 + (y1 - y0) * t, height * iz / nz)))
        rows.append(row)
    for iz in range(nz):
        for ix in range(nx):
            bm.faces.new((rows[iz][ix], rows[iz][ix + 1], rows[iz + 1][ix + 1], rows[iz + 1][ix]))
    ob = _obj("prop_sheer", bm, (0, 0, 0), None, col, smooth_angle=180)
    m = bpy.data.materials.new("orden_sheer")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.92, 0.90, 0.86, 1)
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Alpha"].default_value = 0.5
    b.inputs["Sheen Weight"].default_value = 0.4
    ob.data.materials.append(m)
    return ob


def bedside_styling(col, x, y, z):
    """Dark ceramic vases with dried stems, pebbles and a small wooden bowl."""
    rnd = random.Random(7)
    stone = colour("charcoal_ceramic", (0.22, 0.22, 0.22), 0.55)
    parts = []
    for i, (dx, r, h) in enumerate(((0.0, 0.045, 0.30), (0.075, 0.04, 0.24))):
        parts.append(_set(cylinder(f"prop_vase_{i}", r, r, h, (x + dx, y, z + h / 2), None, col), stone))
    stem_m = colour("dried_stem", (0.42, 0.33, 0.24), 0.8)
    bloom_m = colour("dried_bloom", (0.93, 0.90, 0.84), 0.85)
    for i in range(9):
        a = rnd.uniform(-0.55, 0.55)
        h = rnd.uniform(0.35, 0.55)
        base = Vector((x + rnd.uniform(-0.015, 0.015), y + rnd.uniform(-0.02, 0.02), z + 0.26))
        d = Vector((math.sin(a) * 0.6, rnd.uniform(-0.15, 0.15), math.cos(a))).normalized()
        mid = base + d * h / 2
        st = _set(cylinder(f"prop_stem_{i}", 0.003, 0.002, h, mid, None, col, 8), stem_m)
        st.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        parts += [st, _sphere(f"prop_bloom_{i}", rnd.uniform(0.018, 0.03), base + d * h, col, bloom_m, ico=True)]
    for i, (dx, r) in enumerate(((0.19, 0.035), (0.235, 0.028))):
        parts.append(_sphere(f"prop_pebble_{i}", r, (x + dx, y - 0.02, z + r * 0.55), col, colour("basalt", (0.12, 0.12, 0.12), 0.45), (1.2, 1.0, 0.65)))
    parts.append(_sphere("prop_bowl", 0.045, (x + 0.32, y + 0.02, z + 0.02), col, "oak", (1, 1, 0.45)))
    return group("prop_bedside_styling", col, parts)


def luxe_bed(col, loc, width=1.8, length=2.1):
    """Bed without its own headboard (the wall headboard replaces it); linen
    bedding in grey-beige, layered pillows with one rust velvet cushion."""
    foot = -length / 2
    parts = [
        soft_box("prop_bed_base", (width + 0.04, length, 0.30), (0, 0, 0.17), "linen_grey", col, 0.03),
        hard_box("prop_bed_plinth", (width - 0.2, length - 0.3, 0.03), (0, 0, 0.015), "base", col),
        soft_box("prop_bed_mattress", (width - 0.04, length - 0.06, 0.22), (0, 0, 0.42), "linen_cream", col, 0.05),
        soft_box("prop_bed_duvet", (width + 0.18, length * 0.80, 0.29), (0, foot + length * 0.40 - 0.03, 0.47), "linen_grey", col, 0.09),
        soft_box("prop_bed_duvet_fold", (width + 0.18, 0.30, 0.08), (0, foot + length * 0.80 - 0.17, 0.62), "linen_grey", col, 0.035),
        soft_box("prop_bed_throw", (width + 0.24, 0.62, 0.025), (0, foot + length * 0.47, 0.625), "linen_sand", col, 0.01, level=1),
    ]
    yb = length / 2 - 0.20
    for i, (size, x, y, z, tilt, m) in enumerate((
            ((0.70, 0.18, 0.62), -0.47, yb, 0.82, -12, "linen_cream"),
            ((0.70, 0.18, 0.62), 0.47, yb, 0.82, -12, "linen_cream"),
            ((0.62, 0.17, 0.48), -0.36, yb - 0.17, 0.76, -16, "linen_sand"),
            ((0.62, 0.17, 0.48), 0.36, yb - 0.17, 0.76, -16, "linen_sand"),
            ((0.45, 0.15, 0.42), 0.10, yb - 0.30, 0.74, -18, "linen_cream"))):
        parts.append(soft_box(f"prop_pillow_{i}", size, (x, y, z), m, col, 0.07, rot=(math.radians(tilt), 0, 0)))
    rust = soft_box("prop_pillow_rust", (0.46, 0.14, 0.40), (0.48, yb - 0.32, 0.73), None, col, 0.07, rot=(math.radians(-18), 0, 0))
    parts.append(_set(rust, colour("rust_velvet", (0.55, 0.30, 0.16), 0.55, sheen=0.9)))
    return group("prop_bed", col, parts, loc)


# ====================================================================== dressing

def oak_niche(col, x, y_wall, width=1.6, height=2.45, depth=0.58):
    """Open oak dressing niche: lit shelves, hanging rail, two drawers."""
    t = 0.022
    yc, yf = y_wall - depth / 2, y_wall - depth
    ink = colour("ink", (0.05, 0.05, 0.05), 0.35, metallic=0.7)
    parts = [
        hard_box("prop_niche_side_l", (t, depth, height), (x - width / 2 + t / 2, yc, height / 2), "oak_warm", col, 0.002, "z"),
        hard_box("prop_niche_side_r", (t, depth, height), (x + width / 2 - t / 2, yc, height / 2), "oak_warm", col, 0.002, "z"),
        hard_box("prop_niche_top", (width, depth, t), (x, yc, height - t / 2), "oak_warm", col),
        hard_box("prop_niche_back", (width - 2 * t, 0.012, height - t), (x, y_wall - 0.006, height / 2), "oak_warm", col, 0.001, "z"),
        hard_box("prop_niche_plinth", (width - 2 * t, depth - 0.04, 0.08), (x, yc + 0.02, 0.04), "oak_warm", col),
        hard_box("prop_niche_counter", (width - 2 * t, depth - 0.02, t), (x, yc + 0.01, 0.62), "oak_warm", col),
    ]
    for i, z in enumerate((1.70, 2.02)):
        parts.append(hard_box(f"prop_niche_shelf_{i}", (width - 2 * t, depth - 0.02, t), (x, yc + 0.01, z), "oak_warm", col))
        parts.append(_set(hard_box(f"prop_niche_led_{i}", (width - 2 * t - 0.04, 0.015, 0.006), (x, yf + 0.04, z - t / 2 - 0.003), None, col), emissive(f"led{i}", strength=10)))
    for i, s in enumerate((-1, 1)):
        dx = s * (width / 4 - t / 2)
        parts.append(hard_box(f"prop_niche_drawer_{i}", (width / 2 - t - 0.012, 0.02, 0.17), (x + dx, yf + 0.012, 0.52), "oak_warm", col))
        knob = _set(cylinder(f"prop_niche_knob_{i}", 0.008, 0.008, 0.025, (x + dx, yf - 0.004, 0.52), None, col, 16), ink)
        knob.rotation_euler = (math.radians(90), 0, 0)
        parts.append(knob)
    rail = _set(cylinder("prop_niche_rail", 0.011, 0.011, width - 2 * t, (x, yc, 1.58), None, col, 24), ink)
    rail.rotation_euler = (0, math.radians(90), 0)
    parts.append(rail)
    rnd = random.Random(3)
    fabrics = [colour("garment_a", (0.55, 0.53, 0.50), 0.85, sheen=0.5), colour("garment_b", (0.80, 0.77, 0.72), 0.85, sheen=0.5),
               colour("garment_c", (0.35, 0.33, 0.31), 0.85, sheen=0.5)]
    for i, gx in enumerate((-0.52, -0.38, -0.22, -0.07)):
        h = rnd.uniform(0.62, 0.86)
        g = _set(soft_box(f"prop_garment_{i}", (0.05, 0.44, h), (x + gx, yc, 1.55 - h / 2), None, col, 0.02, level=1), fabrics[i % 3])
        g.rotation_euler = (0, 0, math.radians(rnd.uniform(-6, 6)))
        parts.append(g)
    for i in range(3):
        parts.append(_set(soft_box(f"prop_folded_{i}", (0.34, 0.26, 0.045), (x + 0.32, yc, 0.655 + 0.048 * i), None, col, 0.015), fabrics[(i + 1) % 3]))
    for i, bx in enumerate((-0.35, 0.0)):
        parts.append(hard_box(f"prop_box_{i}", (0.30, 0.32, 0.20), (x + bx, yc + 0.03, 1.81), "white", col, 0.003))
    parts.append(soft_box("prop_niche_pillow", (0.45, 0.30, 0.10), (x - 0.25, yc, 2.09), "linen_cream", col, 0.04))
    return group("prop_niche", col, parts)


def vanity(col, x0, x1, y_wall, z_top=0.76):
    top = hard_box("prop_vanity_top", (x1 - x0, 0.45, 0.03), ((x0 + x1) / 2, y_wall - 0.225, z_top), "marble_warm", col, 0.003)
    m = bpy.data.materials.new("orden_glass")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.5
    leg = _set(hard_box("prop_vanity_leg", (0.012, 0.42, z_top - 0.015), (x1 - 0.03, y_wall - 0.225, (z_top - 0.015) / 2), None, col, 0.001), m)
    return group("prop_vanity", col, [top, leg])


def round_mirror(col, x, y_wall, z, r=0.30):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=r)
    glass = _obj("prop_rmirror_glass", bm, (x, y_wall - 0.03, z), None, col)
    glass.rotation_euler = (math.radians(90), 0, 0)
    mm = bpy.data.materials.new("orden_mirror_r")
    mm.use_nodes = True
    b = mm.node_tree.nodes["Principled BSDF"]
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.02
    glass.data.materials.append(mm)
    bm = bmesh.new()
    seg_major, seg_minor, R, rr = 64, 12, r + 0.012, 0.012
    for i in range(seg_major):
        a = 2 * math.pi * i / seg_major
        for j in range(seg_minor):
            b2 = 2 * math.pi * j / seg_minor
            bm.verts.new(((R + rr * math.cos(b2)) * math.cos(a), (R + rr * math.cos(b2)) * math.sin(a), rr * math.sin(b2)))
    bm.verts.ensure_lookup_table()
    for i in range(seg_major):
        for j in range(seg_minor):
            v = lambda ii, jj: bm.verts[(ii % seg_major) * seg_minor + (jj % seg_minor)]
            bm.faces.new((v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)))
    ring = _obj("prop_rmirror_ring", bm, (x, y_wall - 0.03, z), None, col, smooth_angle=180)
    ring.rotation_euler = (math.radians(90), 0, 0)
    ring.data.materials.append(emissive("mirror_ring", (1.0, 0.85, 0.65), 5.0))
    return group("prop_round_mirror", col, [glass, ring])


def pouf(col, loc):
    p = _set(soft_box("prop_pouf", (0.46, 0.46, 0.42), (0, 0, 0.21), None, col, 0.2, level=3), colour("blush_velvet", (0.80, 0.62, 0.55), 0.6, sheen=1.0))
    return group("prop_pouf_g", col, [p], loc)


def dark_bench(col, loc, length=1.5, rot_z=0.0):
    frame_m = colour("bronze_lacquer", (0.29, 0.24, 0.21), 0.45, coat=0.2)
    t = 0.035
    parts = [_set(hard_box("prop_dbench_top", (length, 0.42, t), (0, 0, 0.42 - t / 2), None, col, 0.002), frame_m),
             _set(hard_box("prop_dbench_shelf", (length, 0.42, t), (0, 0, 0.06), None, col, 0.002), frame_m)]
    for sx in (-1, 1):
        parts.append(_set(hard_box(f"prop_dbench_side_{sx}", (t, 0.42, 0.42), (sx * (length / 2 - t / 2), 0, 0.21), None, col, 0.002), frame_m))
    parts.append(soft_box("prop_dbench_cushion", (length * 0.48, 0.38, 0.11), (-length * 0.22, 0, 0.47), "linen_cream", col, 0.05))
    parts.append(soft_box("prop_dbench_folded", (0.36, 0.26, 0.10), (0.35, 0, 0.13), "linen_grey", col, 0.03))
    return group("prop_dark_bench", col, parts, loc, rot_z)


def striped_rug(col, size, loc):
    ob = hard_box("prop_rug_striped", (size[0], size[1], 0.012), (loc[0], loc[1], 0.006), None, col, 0.004)
    m = bpy.data.materials.new("orden_rug_stripes")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 18
    wave.inputs["Distortion"].default_value = 0.4
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (*rk.mats._lin((0.62, 0.60, 0.57)), 1)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (*rk.mats._lin((0.90, 0.88, 0.84)), 1)
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Sheen Weight"].default_value = 0.6
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 400
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    ob.data.materials.append(m)
    return ob


def ceiling_slots(col, segments, y, H):
    for i, (x0, x1) in enumerate(segments):
        _set(hard_box(f"prop_ceiling_slot_{i}", (x1 - x0, 0.03, 0.01), ((x0 + x1) / 2, y, H - 0.006), None, col), emissive(f"slot{i}", (1.0, 0.86, 0.68), 14.0))


# ======================================================================== living

def panel_wall(col, x0, x1, z0, z1, y_wall, pw=0.34, ph=0.50, gap=0.04):
    """Dark walnut wall of rounded-rectangle relief panels (coffee-table photo)."""
    cols = int((x1 - x0) // (pw + gap))
    rows = int((z1 - z0) // (ph + gap))
    ox = x0 + ((x1 - x0) - cols * (pw + gap)) / 2
    parts = [hard_box("prop_panelwall_back", (x1 - x0, 0.02, z1 - z0), ((x0 + x1) / 2, y_wall - 0.01, (z0 + z1) / 2), "walnut", col, 0.001, "z")]
    rot = Matrix.Rotation(math.radians(90), 3, "X")
    for c in range(cols):
        for r in range(rows):
            bm = bp.slab_bmesh((pw, ph, 0.035), 0.07, 0.008, corner_segments=8, edge_segments=3)
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
            parts.append(_obj(f"prop_panel_{c}_{r}", bm, (ox + gap / 2 + c * (pw + gap) + pw / 2, y_wall - 0.02 - 0.0175, z0 + gap / 2 + r * (ph + gap) + ph / 2), "walnut", col, grain="z"))
    return group("prop_panel_wall", col, parts)


def sectional_sofa(col, loc, length=3.3, depth=1.0, chaise=1.6):
    """Large cream sofa with a rounded chaise end on the right (photo reference)."""
    m = "linen_cream"
    parts = [
        soft_box("prop_sect_base", (length, depth, 0.32), (0, 0, 0.20), m, col, 0.07),
        soft_box("prop_sect_back", (length - 0.95, 0.30, 0.44), (-0.475, depth / 2 - 0.16, 0.60), m, col, 0.11),
        soft_box("prop_sect_arm_l", (0.28, depth, 0.58), (-length / 2 + 0.14, 0, 0.33), m, col, 0.11),
    ]
    seat_w = (length - 0.28 - 0.95) / 2
    for i in range(2):
        parts.append(soft_box(f"prop_sect_seat_{i}", (seat_w - 0.01, depth - 0.30, 0.15), (-length / 2 + 0.28 + seat_w * (i + 0.5), -0.06, 0.43), m, col, 0.07))
    bm = bp.slab_bmesh((0.95, chaise, 0.46), 0.42, 0.10, corner_segments=16, edge_segments=5)
    ch = _obj("prop_sect_chaise", bm, (length / 2 - 0.475, depth / 2 - chaise / 2, 0.23), m, col)
    ch.data.materials.clear()
    ch.data.materials.append(rk.mats.material(m))
    sub = ch.modifiers.new("soft", "SUBSURF")
    sub.levels = sub.render_levels = 1
    parts.append(ch)
    parts.append(soft_box("prop_sect_back_r", (0.95, 0.30, 0.40), (length / 2 - 0.475, depth / 2 - 0.16, 0.62), m, col, 0.11))
    cush = soft_box("prop_sect_cushion", (0.48, 0.14, 0.44), (-1.15, depth / 2 - 0.36, 0.66), None, col, 0.08, rot=(math.radians(-12), 0, 0.2))
    parts.append(_set(cush, colour("olive_velvet", (0.22, 0.27, 0.16), 0.6, sheen=1.0)))
    parts.append(hard_box("prop_sect_plinth", (length - 0.3, depth - 0.3, 0.04), (0, 0, 0.02), "walnut", col))
    return group("prop_sectional", col, parts, loc)


def table_styling(col, top_z, x, y):
    """Coffee-table styling after the reference: vase with leafy branches,
    two books, a small dark bowl with a wooden sphere."""
    rnd = random.Random(11)
    parts = []
    stem_m = colour("branch", (0.30, 0.22, 0.16), 0.8)
    leaf_m = colour("leaf", (0.35, 0.42, 0.24), 0.7, sheen=0.3)
    vx, vy = x - 0.18, y + 0.15
    for i in range(7):
        a = rnd.uniform(-0.6, 0.6)
        h = rnd.uniform(0.30, 0.48)
        base = Vector((vx, vy, top_z + 0.22))
        d = Vector((math.sin(a) * 0.7, rnd.uniform(-0.2, 0.2), math.cos(a))).normalized()
        st = _set(cylinder(f"prop_branch_{i}", 0.003, 0.002, h, base + d * h / 2, None, col, 8), stem_m)
        st.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        parts.append(st)
        for j in range(6):
            p = base + d * h * (0.35 + j * 0.12) + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0))
            parts.append(_sphere(f"prop_leaf_{i}_{j}", 0.012, p, col, leaf_m, (1.6, 0.6, 0.8), ico=True))
    parts.append(rk.books(col, (x + 0.18, y - 0.05, top_z), rot_z=-0.35))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=0.08, radius2=0.12, depth=0.04)
    parts.append(_set(_obj("prop_dark_bowl", bm, (x - 0.12, y - 0.16, top_z + 0.02), None, col), colour("basalt", (0.12, 0.12, 0.12), 0.4)))
    parts.append(_sphere("prop_wood_sphere", 0.045, (x - 0.12, y - 0.16, top_z + 0.085), col, "walnut"))
    return parts
