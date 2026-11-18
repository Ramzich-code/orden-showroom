"""
ORDEN — Collection 001 product models (Blender 4.5, run headless).

    blender -b --factory-startup --python blender/products/build_products.py

Builds the three commercial products as real, bevelled meshes with
world-scale UVs, one object per physical component, each parented to a
product root empty placed at the footprint centre on the floor.

Conventions (shared with the website):
  * metres, Z up in Blender (the glTF exporter converts to Y up)
  * product front faces -Y in Blender (= +Z on the web after conversion)
  * object names == component ids in src/config/products.ts
  * each object carries a custom property "role" (body, travertine, marble,
    base, accent, metal, interior) that the material system and the website
    use to assign finishes; geometry never changes between finishes
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDERS = {}  # filled below: product id -> build function

# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #

EPS = 1e-5


def _box_bmesh(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    return bm


def _bevel(bm, edges, offset, segments, profile=0.5):
    if not edges or offset <= 0:
        return
    bmesh.ops.bevel(
        bm,
        geom=edges,
        offset=offset,
        offset_type="OFFSET",
        profile_type="SUPERELLIPSE",
        segments=segments,
        profile=profile,
        affect="EDGES",
        clamp_overlap=True,
        harden_normals=False,
    )


def _vertical_edges(bm):
    out = []
    for e in bm.edges:
        a, b = e.verts[0].co, e.verts[1].co
        if abs(a.x - b.x) < EPS and abs(a.y - b.y) < EPS:
            out.append(e)
    return out


def _cap_edges(bm, z_top, z_bot):
    out = []
    for e in bm.edges:
        za, zb = e.verts[0].co.z, e.verts[1].co.z
        if (abs(za - z_top) < EPS and abs(zb - z_top) < EPS) or (abs(za - z_bot) < EPS and abs(zb - z_bot) < EPS):
            out.append(e)
    return out


def slab_bmesh(size, corner_radius, edge_radius, corner_segments=12, edge_segments=4, bottom_edge=None):
    """Rounded-rectangle slab: large plan radius on the vertical corners,
    small eased radius on the top (and bottom) perimeter."""
    sx, sy, sz = size
    bm = _box_bmesh(sx, sy, sz)
    _bevel(bm, _vertical_edges(bm), corner_radius, corner_segments)
    top, bot = sz / 2, -sz / 2
    if bottom_edge is None:
        bottom_edge = edge_radius
    # top and bottom perimeters may want different radii
    top_edges = [e for e in _cap_edges(bm, top, bot) if abs(e.verts[0].co.z - top) < EPS]
    _bevel(bm, top_edges, edge_radius, edge_segments)
    bot_edges = [e for e in _cap_edges(bm, top, bot) if abs(e.verts[0].co.z - bot) < EPS]
    _bevel(bm, bot_edges, bottom_edge, max(2, edge_segments - 1))
    return bm


def panel_bmesh(size, edge_radius=0.0015, segments=2):
    """Board with a small eased arris on every edge (no razor-sharp CG edges)."""
    bm = _box_bmesh(*size)
    _bevel(bm, list(bm.edges), edge_radius, segments)
    return bm


def leg_bmesh(r_top, r_bottom, height, segments=40):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r_bottom, radius2=r_top, depth=height)
    rim = [e for e in bm.edges if e.is_boundary is False and len(e.link_faces) == 2
           and abs(abs(e.verts[0].co.z) - height / 2) < EPS and abs(abs(e.verts[1].co.z) - height / 2) < EPS]
    _bevel(bm, rim, 0.002, 2)
    return bm


def box_uv(bm, grain="x", scale=1.0):
    """World-scale box projection (1 UV unit = 1 m / scale).
    `grain` is the object axis the wood grain / stone bedding runs along;
    it is always mapped to U so all wood textures can share one orientation."""
    uv = bm.loops.layers.uv.verify()
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            c = loop.vert.co
            if ax == 2:  # top / bottom
                u, v = (c.x, c.y) if grain != "y" else (c.y, c.x)
                if grain == "z":
                    u, v = c.x, c.y
            elif ax == 1:  # front / back
                u, v = (c.x, c.z) if grain != "z" else (c.z, c.x)
            else:  # sides
                u, v = (c.y, c.z) if grain != "z" else (c.z, c.y)
            loop[uv].uv = (u * scale, v * scale)


def make_object(name, bm, location, parent, role, grain="x", collection=None):
    box_uv(bm, grain)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    try:
        mesh.set_sharp_from_angle(angle=math.radians(35))
    except AttributeError:  # older API
        pass
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.location = location
    obj.parent = parent
    obj["role"] = role
    obj["grain"] = grain
    # keep large flat faces perfectly flat next to rounded bevels
    wn = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    wn.keep_sharp = True
    wn.weight = 50
    return obj


def notch(obj, centre, size):
    """Cut a rectangular notch (world-space centre/size) out of obj, then
    restore world-scale UVs and ease the freshly cut edges."""
    bpy.context.view_layer.update()
    cutter = bpy.data.objects.new("_cutter", bpy.data.meshes.new("_cutter"))
    bm = _box_bmesh(*size)
    bm.to_mesh(cutter.data)
    bm.free()
    bpy.context.scene.collection.objects.link(cutter)
    cutter.location = centre
    bpy.context.view_layer.update()
    for m in list(obj.modifiers):
        obj.modifiers.remove(m)
    mod = obj.modifiers.new("notch", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    bpy.context.view_layer.objects.active = obj
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    box_uv(bm, obj.get("grain", "x"))
    bm.to_mesh(obj.data)
    bm.free()
    for p in obj.data.polygons:
        p.use_smooth = True
    bev = obj.modifiers.new("EaseCut", "BEVEL")
    bev.width = 0.0015
    bev.segments = 2
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(60)
    bev.harden_normals = False
    wn = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    wn.keep_sharp = True
    wn.weight = 50


def make_root(name, collection):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.2
    collection.objects.link(root)
    root["orden_product"] = name
    return root


def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


# --------------------------------------------------------------------------- #
# PRODUCT 01 — Lune Coffee Table  (rev. 7 — client front-view sketch)
#
# DESIGN RULES (client):
#   * the upper (travertine) and lower (walnut) platforms are the SAME slab:
#     identical width, depth, thickness, corner radius, edge profile
#   * in front view both slabs start and end at the same place (aligned)
#   * one walnut panel stands OUTSIDE the left ends of both slabs, touching
#     them, from the floor up into the thickness of the upper slab
#   * the lower slab is carried by the panel (raised off the floor)
#   * the space between the slabs is open; no other support
#
# Heights and the panel's span solved against the original photograph under
# these rules (blender/products/fit_outboard.py, rms ~10 px):
#   slab        1.10 x 1.02 x 0.07 m, plan corner radius 0.18 m
#   lower slab  underside 0.031 m above the floor
#   upper slab  underside 0.219 m  -> open space 0.118 m between slabs
#   panel       30 x 238 mm, floor to 0.263 m, centred 82 mm in front of
#               mid-depth, against the slab ends
# Absolute scale assumed (slab length 1.10 m); the photo has no dimension.
# --------------------------------------------------------------------------- #

COFFEE = dict(
    slab_w=1.10, slab_d=1.02, slab_t=0.07, slab_r=0.18,
    slab_edge_top=0.02, slab_edge_bottom=0.015,
    upper_under=0.219, lower_under=0.031,
    panel_t=0.03, panel_top=0.263, panel_y_back=0.037, panel_y_front=-0.201,
)


def coffee_top_z():
    return COFFEE["upper_under"] + COFFEE["slab_t"]


def coffee_slab_bmesh():
    """The one platform shape, used for both levels."""
    c = COFFEE
    return slab_bmesh((c["slab_w"], c["slab_d"], c["slab_t"]), c["slab_r"], c["slab_edge_top"],
                      corner_segments=20, edge_segments=6, bottom_edge=c["slab_edge_bottom"])


def build_coffee_table(col):
    c = COFFEE
    root = make_root("coffee-table", col)
    # Blender axes: +X right, -Y front, +Z up. Both slabs share the same plan position.
    make_object("top", coffee_slab_bmesh(), (0, 0, c["upper_under"] + c["slab_t"] / 2), root, "travertine", "x", col)
    make_object("platform", coffee_slab_bmesh(), (0, 0, c["lower_under"] + c["slab_t"] / 2), root, "body", "x", col)
    pw = c["panel_y_back"] - c["panel_y_front"]
    px = -c["slab_w"] / 2 - c["panel_t"] / 2          # outside the slab ends, touching them
    make_object("panel", panel_bmesh((c["panel_t"], pw, c["panel_top"]), 0.003, 3),
                (px, (c["panel_y_back"] + c["panel_y_front"]) / 2, c["panel_top"] / 2), root, "body", "z", col)
    return root


# --------------------------------------------------------------------------- #
# PRODUCT 02 — Hvile Bedside Table
# Reference: taupe carcass whose sides and back rise ~2 cm above an inset
# white marble top; open shelf; large handleless drawer; dark recessed plinth.
# --------------------------------------------------------------------------- #

# Proportions measured on the reference photograph with a solved camera
# (blender/products/fit_bedside.py: level two-point perspective, rms 1.6 px).
# Scale: frame height 0.50 m. The photo does not fix the width (0.60-1.07 m all
# fit); the client chose 60 x 55 cm (2026-11-17) so it reads as a bedside table.
BEDSIDE = dict(
    W=0.60, D=0.55, H=0.50, t=0.022, back_t=0.018,
    side_z0=0.04,                     # side panels stop ~4 cm above the floor
    plinth_h=0.055, plinth_inset=0.05,  # dark recessed base under the carcass
    drawer_z0=0.058, drawer_z1=0.295,
    shelf_z0=0.300, shelf_z1=0.320,
    marble_z0=0.450, marble_z1=0.480,   # frame stands 20 mm proud of the marble
)


def build_bedside_table(col):
    c = BEDSIDE
    root = make_root("bedside-table", col)
    W, D, H, t = c["W"], c["D"], c["H"], c["t"]
    inner_w = W - 2 * t
    front = -D / 2
    inner_d = D - c["back_t"]
    y_inner = front + inner_d / 2
    side_h = H - c["side_z0"]

    make_object("side-l", panel_bmesh((t, D, side_h), 0.0018), (-W / 2 + t / 2, 0, c["side_z0"] + side_h / 2), root, "body", "z", col)
    make_object("side-r", panel_bmesh((t, D, side_h), 0.0018), (W / 2 - t / 2, 0, c["side_z0"] + side_h / 2), root, "body", "z", col)
    back_h = H - c["plinth_h"]
    make_object("back", panel_bmesh((inner_w, c["back_t"], back_h), 0.0015), (0, D / 2 - c["back_t"] / 2, c["plinth_h"] + back_h / 2), root, "body", "z", col)
    make_object("bottom", panel_bmesh((inner_w, inner_d, 0.02), 0.0012), (0, y_inner, c["plinth_h"] + 0.01), root, "body", "x", col)
    make_object("shelf", panel_bmesh((inner_w, inner_d - 0.004, c["shelf_z1"] - c["shelf_z0"]), 0.0015),
                (0, y_inner + 0.002, (c["shelf_z0"] + c["shelf_z1"]) / 2), root, "body", "x", col)
    mh = c["marble_z1"] - c["marble_z0"]
    make_object("top", slab_bmesh((inner_w - 0.002, inner_d - 0.002, mh), 0.003, 0.0025, corner_segments=3, edge_segments=3),
                (0, y_inner, c["marble_z0"] + mh / 2), root, "marble", "x", col)
    dh = c["drawer_z1"] - c["drawer_z0"]
    make_object("drawer-front", panel_bmesh((inner_w - 0.004, 0.02, dh), 0.0018),
                (0, front + 0.012, c["drawer_z0"] + dh / 2), root, "body", "x", col)
    make_object("drawer-box", panel_bmesh((inner_w - 0.03, inner_d - 0.06, dh - 0.045), 0.001),
                (0, y_inner + 0.03, c["drawer_z0"] + (dh - 0.045) / 2 + 0.012), root, "interior", "x", col)
    pi = c["plinth_inset"]
    make_object("plinth", panel_bmesh((W - 2 * pi, D - pi - 0.03, c["plinth_h"]), 0.001),
                (0, (pi - 0.03) / 2, c["plinth_h"] / 2), root, "base", "x", col)
    return root


# --------------------------------------------------------------------------- #
# PRODUCT 03 — Fjell Wardrobe (approved design, details matched to the
# Warm Minimalism image): ~1.08 m wide, two flush doors set BETWEEN the side
# panels, whose outer front and top edges are generously rounded; short vertical pulls near the
# centre seam (~35 cm, centred ~1.04 m); full-width shelf and steel rail
# inside; short tapered legs (~6 cm).
# --------------------------------------------------------------------------- #

WARDROBE = dict(W=1.08, D=0.58, H=1.95, legs=0.06, side_t=0.055, side_round=0.045,
                door_t=0.022, pull_len=0.35, pull_z=1.04, pull_dx=0.05)


def build_wardrobe(col):
    c = WARDROBE
    root = make_root("wardrobe", col)
    W, D, H, Y0, T, dt = c["W"], c["D"], c["H"], c["legs"], c["side_t"], c["door_t"]
    front = -D / 2

    def side(name, x, outer_sign):
        bm = _box_bmesh(T, D, H)
        # round the outer-front vertical edge and the outer-top edge generously
        # (one bevel, so they blend into a soft corner), the rest just eased
        ox = outer_sign * T / 2
        e_front = [e for e in bm.edges
                   if all(abs(v.co.x - ox) < EPS for v in e.verts)
                   and (all(abs(v.co.y + D / 2) < EPS for v in e.verts) or all(abs(v.co.z - H / 2) < EPS for v in e.verts))]
        _bevel(bm, e_front, c["side_round"], 10)
        _bevel(bm, [e for e in bm.edges if e.calc_length() > 0.05 and e not in e_front and not e.is_wire], 0.0015, 2)
        return make_object(name, bm, (x, 0, Y0 + H / 2), root, "body", "z", col)

    side("side-l", -W / 2 + T / 2, -1)
    side("side-r", W / 2 - T / 2, +1)
    inner_w = W - 2 * T
    carcass_d = D - dt                      # doors sit in front of the carcass, between the sides
    cy = front + dt + carcass_d / 2
    make_object("top", panel_bmesh((inner_w, carcass_d, 0.019)), (0, cy, Y0 + H - 0.0095), root, "body", "x", col)
    make_object("base", panel_bmesh((inner_w, carcass_d, 0.019)), (0, cy, Y0 + 0.0095), root, "body", "x", col)
    make_object("back", panel_bmesh((inner_w, 0.008, H - 0.038), 0.0008), (0, D / 2 - 0.004, Y0 + H / 2), root, "body", "z", col)
    make_object("shelf", panel_bmesh((inner_w, carcass_d - 0.05, 0.019)), (0, cy + 0.02, Y0 + H - 0.34), root, "interior", "x", col)
    rail = leg_bmesh(0.013, 0.013, inner_w - 0.01, 32)
    bmesh.ops.rotate(rail, verts=rail.verts, cent=(0, 0, 0), matrix=__import__("mathutils").Matrix.Rotation(math.radians(90), 3, "Y"))
    make_object("rail", rail, (0, cy, Y0 + H - 0.42), root, "metal", "x", col)

    door_w = inner_w / 2 - 0.002
    for name, x in (("door-l", -inner_w / 4 - 0.0005), ("door-r", inner_w / 4 + 0.0005)):
        bm = _box_bmesh(door_w, dt, H - 0.004)
        _bevel(bm, list(bm.edges), 0.002, 2)
        make_object(name, bm, (x, front + dt / 2, Y0 + H / 2), root, "body", "z", col)
    for name, x in (("handle-l", -c["pull_dx"]), ("handle-r", c["pull_dx"])):
        bm = _box_bmesh(0.016, 0.022, c["pull_len"])
        _bevel(bm, list(bm.edges), 0.006, 4)
        make_object(name, bm, (x, front - 0.011, c["pull_z"]), root, "accent", "z", col)
    for k, sx, sy in (("fl", -1, -1), ("fr", 1, -1), ("bl", -1, 1), ("br", 1, 1)):
        make_object(f"leg-{k}", leg_bmesh(0.018, 0.013, Y0), (sx * (W / 2 - 0.07), sy * (D / 2 - 0.07), Y0 / 2), root, "accent", "z", col)
    return root


# --------------------------------------------------------------------------- #

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    s.unit_settings.scale_length = 1.0


BUILDERS.update({
    "coffee-table": build_coffee_table,
    "bedside-table": build_bedside_table,
    "wardrobe": build_wardrobe,
})


def verify_identical_slabs(root):
    """Assert the two platforms share exactly the same base mesh geometry."""
    import numpy as np
    objs = {c.name: c for c in root.children}
    meshes = [objs["top"].data, objs["platform"].data]
    counts = [(len(m.vertices), len(m.edges), len(m.polygons)) for m in meshes]
    co = []
    for m in meshes:
        a = np.empty(len(m.vertices) * 3)
        m.vertices.foreach_get("co", a)
        co.append(a.reshape(-1, 3))
    same_topology = counts[0] == counts[1]
    max_diff = float(np.abs(co[0] - co[1]).max()) if same_topology else float("inf")
    dims = [tuple(round(v, 4) for v in (o.dimensions)) for o in (objs["top"], objs["platform"])]
    print(f"[VERIFY] topology top={counts[0]} platform={counts[1]} identical={same_topology}")
    print(f"[VERIFY] max vertex difference (local space): {max_diff:.2e} m")
    print(f"[VERIFY] dimensions top={dims[0]} platform={dims[1]}")
    off = objs["platform"].location - objs["top"].location
    print(f"[VERIFY] platform offset from top: dx={off.x:+.3f} dy={off.y:+.3f} dz={off.z:+.3f} m")
    assert same_topology and max_diff < 1e-9, "platforms are not identical"


def build_one(pid):
    """Fresh scene containing only this product (object names are global in a
    .blend, so each product lives in its own file: <id>.blend)."""
    reset_scene()
    return BUILDERS[pid](new_collection(pid))


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDERS)
    for pid in only:
        root = build_one(pid)
        parts = [c.name for c in root.children]
        print(f"[ORDEN] {pid}: {len(parts)} components -> {', '.join(sorted(parts))}")
        if pid == "coffee-table":
            verify_identical_slabs(root)
        if "--no-save" not in sys.argv:
            path = os.path.join(HERE, f"{pid}.blend")
            bpy.ops.wm.save_as_mainfile(filepath=path)
            print("[ORDEN] saved", path)
