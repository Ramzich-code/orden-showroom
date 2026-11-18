"""
ORDEN scroll journey: the camera moves the website plays while you scroll.

    blender -b --factory-startup --python blender/journey/journey.py -- [exterior living bedroom storage] [samples] [WxH] [portrait]

Segments:
  exterior  golden-hour approach to the ORDEN house, ending at the glazing
  living / bedroom / storage
            a glide through the room that ENDS EXACTLY on the room's cam_room
            (cam_room_p in portrait), so the interactive stage (stills + live
            pieces) takes over from the last frame without a jump

Frames: blender/renders/journey/<segment>[-p]/f_####.png (web versions are
made by `npm run assets`). The room segments load the approved room files and
only add a camera: nothing in the rooms is changed or re-saved.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOMS_DIR = os.path.join(HERE, "..", "rooms")
sys.path.insert(0, ROOMS_DIR)
import room_kit as rk  # noqa: E402
import room_props as rp  # noqa: E402
import rooms  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "renders", "journey"))
FRAMES = {"exterior": 72, "living": 60, "bedroom": 60, "storage": 60}
EXPOSURE = dict(rooms.EXPOSURE, exterior=0.35)
RESUME = False

# Room glides: (start location, start target, start lens) -> the room camera.
# Landscape cameras end on cam_room, portrait on cam_room_p.
GLIDE = {
    "living": ((1.5, -2.2, 2.05), (-1.3, 1.7, 0.55), 24),
    "bedroom": ((1.55, -1.9, 1.65), (-0.7, 1.6, 0.75), 22),
    "storage": ((2.05, -1.85, 1.75), (0.7, 1.7, 1.0), 22),
}
GLIDE_P = {
    "living": ((0.9, -2.25, 2.3), (-0.9, 1.4, 0.3), 19),
    "bedroom": ((0.9, -2.0, 1.7), (-0.5, 1.8, 0.5), 18),
    "storage": ((1.6, -1.95, 1.7), (0.4, 1.8, 0.9), 17),
}


# --------------------------------------------------------------------------- camera

def keyed_camera(name, frames, start, end):
    """Camera that tracks an animated target; both ease in and out. start/end:
    (location, target, lens). The end pose is exactly rk.camera(end...)."""
    cd = bpy.data.cameras.new(name)
    cd.sensor_width = 36
    cam = bpy.data.objects.new(name, cd)
    tgt = bpy.data.objects.new(f"{name}_target", None)
    for o in (cam, tgt):
        bpy.context.scene.collection.objects.link(o)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for f, (loc, target, lens) in ((1, start), (frames, end)):
        cam.location = loc
        tgt.location = target
        cd.lens = lens
        cam.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
    for ob in (cam, tgt, cd):
        ad = ob.animation_data
        for fc in ad.action.fcurves if hasattr(ad.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "AUTO"
    bpy.context.scene.camera = cam
    return cam


def room_end_pose(room, portrait):
    """cam_room / cam_room_p as (location, target, lens), from rooms.py / portrait.py."""
    cam = bpy.data.objects["cam_room_p" if portrait else "cam_room"]
    fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    return tuple(cam.location), tuple(cam.location + fwd * 3.0), cam.data.lens


# --------------------------------------------------------------------------- exterior

def exterior():
    """The ORDEN house at golden hour: white plaster volume, walnut-clad wing,
    a wide glazing onto a warm living room (Mjuk sofa, Lune table), travertine
    terrace, planters. Front faces -Y."""
    col = rk.new_scene()
    W, Dh, H = 12.0, 8.0, 3.3
    gx0, gx1, gz1 = -1.6, 2.6, 2.8          # glazing
    dx0, dx1, dz1 = -3.7, -2.5, 2.45        # entrance door
    t = 0.25
    # front wall around the openings
    blocks = [(-W / 2, dx0, 0, H), (dx1, gx0, 0, H), (gx1, 2.9, 0, H),
              (dx0, dx1, dz1, H), (gx0, gx1, gz1, H)]
    for i, (x0, x1, z0, z1) in enumerate(blocks):
        rk.hard_box(f"ext_front_{i}", (x1 - x0, t, z1 - z0), ((x0 + x1) / 2, -t / 2, (z0 + z1) / 2), "plaster_white", col)
    # walnut-clad wing with vertical slats
    rk.hard_box("ext_clad_back", (W / 2 - 2.9, t, H), ((2.9 + W / 2) / 2, -t / 2, H / 2), "base", col)
    n = 34
    for i in range(n):
        x = 2.95 + (W / 2 - 3.0) * (i + 0.5) / n
        rk.hard_box(f"ext_slat_{i}", (0.07, 0.04, H - 0.02), (x, -t - 0.02, H / 2), "walnut", col)
    # side and back walls, floor, roof
    rk.hard_box("ext_side_l", (t, Dh, H), (-W / 2 + t / 2, Dh / 2, H / 2), "plaster_white", col)
    rk.hard_box("ext_side_r", (t, Dh, H), (W / 2 - t / 2, Dh / 2, H / 2), "plaster_white", col)
    rk.hard_box("ext_back", (W, t, H), (0, Dh - t / 2, H / 2), "plaster", col)
    rk.hard_box("ext_floor_in", (W, Dh, 0.04), (0, Dh / 2, -0.02), "floor", col)
    rk.hard_box("ext_roof", (W + 1.2, Dh + 1.2, 0.32), (0, Dh / 2 - 0.3, H + 0.16), "plaster_white", col)
    rk.hard_box("ext_ceiling_in", (W, Dh, 0.02), (0, Dh / 2, H - 0.01), "plaster_white", col)
    # glazing: slim dark frames, clear glass
    glass = bpy.data.materials.new("ext_glass")
    glass.use_nodes = True
    b = glass.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.45
    pane = rk.hard_box("ext_glass", (gx1 - gx0, 0.012, gz1 - 0.02), ((gx0 + gx1) / 2, -0.12, gz1 / 2 + 0.01), None, col)
    pane.data.materials.clear()
    pane.data.materials.append(glass)
    # a flat pane: smoothed normals on a thin box act like a lens (barrel distortion, sun hotspot)
    for m in list(pane.modifiers):
        pane.modifiers.remove(m)
    for poly in pane.data.polygons:
        poly.use_smooth = False
    for i, x in enumerate((gx0, gx1)):                       # frameless centre: one wide pane
        rk.hard_box(f"ext_mullion_{i}", (0.05, 0.08, gz1), (x, -0.12, gz1 / 2), "base", col)
    rk.hard_box("ext_glass_head", (gx1 - gx0, 0.08, 0.05), ((gx0 + gx1) / 2, -0.12, gz1), "base", col)
    # door fills its opening: no gap for the low sun to project a pinhole spot inside
    rk.hard_box("ext_door", (dx1 - dx0 + 0.02, 0.06, dz1 + 0.01), ((dx0 + dx1) / 2, -0.08, dz1 / 2), "walnut", col)
    rk.hard_box("ext_door_pull", (0.025, 0.04, 0.9), (dx1 - 0.18, -0.13, 1.05), "base", col)
    # inside, seen through the glass: the living room pieces in warm light
    rk.place_product("sofa", (0.5, 4.6, 0))
    rk.place_product("coffee-table", (0.4, 2.9, 0))
    rk.rug(col, (3.6, 2.6), (0.4, 3.4))
    for lt in (rk._area("ext_inside_light", (3.0, 2.0), (0.4, 3.4, H - 0.1), (0, 0, -1), 900, (1.0, 0.8, 0.6)),
               rk._area("ext_inside_fill", (4.0, 2.4), (0.4, 7.6, 1.6), (0, -1, 0), 250, (1.0, 0.85, 0.7))):
        # light the room, never seen as a panel (also not through the glass)
        lt.visible_camera = lt.visible_transmission = lt.visible_glossy = False
    rp.pendant(col, 0.4, 2.9, 1.95, ceiling=H)
    # terrace, steps down to the lawn, planters
    rk.hard_box("ext_terrace", (W + 2, 4.5, 0.18), (0, -2.25 - t, -0.09), "travertine", col)
    rk.hard_box("ext_step", (4.0, 0.4, 0.09), (0.4, -4.95 - t, -0.135), "travertine", col)
    lawn = rk.hard_box("ext_lawn", (80, 80, 0.02), (0, -30, -0.19), None, col)
    rp._set(lawn, rp.colour("lawn", (0.30, 0.34, 0.20), 0.95, sheen=0.4))
    for i, x in enumerate((-5.2, 4.9, -0.9)):
        rk.cylinder(f"ext_pot_{i}", 0.34, 0.3, 0.7, (x, -1.3, 0.35), None, col)
        pot = bpy.data.objects[f"ext_pot_{i}"]
        rp._set(pot, rp.colour("pot_stone", (0.32, 0.30, 0.27), 0.85))
        shrub = rp._sphere(f"ext_shrub_{i}", 0.46, (x, -1.3, 1.05), col, rp.colour("olive", (0.30, 0.34, 0.19), 0.85, sheen=0.6), (1, 1, 1.1))
        for poly in shrub.data.polygons:
            poly.use_smooth = True
    # golden hour: low warm sun from the front-left, soft sky
    sun = rk.daylight(sun_rot_deg=(79, 0, -38), sun_strength=3.4, hdri_strength=0.55, hdri_rot=150)
    sun.data.color = (1.0, 0.68, 0.40)
    sun.data.angle = math.radians(2.5)
    # warm the sky towards sunset (the garden HDRI is a midday sky)
    w = bpy.context.scene.world
    nt = w.node_tree
    env = next(n for n in nt.nodes if n.type == "TEX_ENVIRONMENT")
    bg = nt.nodes["Background"]
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 0.55
    hs.inputs["Value"].default_value = 0.85
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    mix.inputs["Color2"].default_value = (1.0, 0.74, 0.50, 1)
    nt.links.new(env.outputs["Color"], hs.inputs["Color"])
    nt.links.new(hs.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(mix.outputs["Color"], bg.inputs["Color"])
    return col


# --------------------------------------------------------------------------- render

def render_segment(name, samples, res, portrait):
    frames = FRAMES[name]
    if name == "exterior":
        exterior()
        start = ((-0.4, -13.5, 1.45), (0.6, 2.0, 1.55), 32) if not portrait else ((0.3, -8.8, 1.55), (0.5, 2.0, 1.9), 26)
        end = ((0.45, -1.7, 1.45), (0.45, 4.0, 1.15), 28) if not portrait else ((0.45, -1.7, 1.45), (0.45, 4.0, 1.15), 20)
    else:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOMS_DIR, f"{name}.blend"))
        start = (GLIDE_P if portrait else GLIDE)[name]
        end = room_end_pose(name, portrait)
    keyed_camera("cam_journey", frames, start, end)
    rk.preview_settings(samples=samples, res=res, exposure=EXPOSURE[name])
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, frames
    s.render.fps = 24
    s.cycles.use_denoising = True
    out = os.path.join(OUT, f"{name}-p" if portrait else name)
    os.makedirs(out, exist_ok=True)
    s.render.filepath = os.path.join(out, "f_")
    s.render.image_settings.file_format = "PNG"
    # "resume": keep the frames already rendered (after an interrupted run)
    s.render.use_overwrite = not RESUME
    s.render.use_placeholder = RESUME
    if name == "exterior":
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "exterior.blend"))
    bpy.ops.render.render(animation=True)
    print("[ORDEN] journey", name, "portrait" if portrait else "landscape", frames, "frames ->", out)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = [a for a in args if a in FRAMES] or list(FRAMES)
    samples = next((int(a) for a in args if a.isdigit()), 16)
    portrait = "portrait" in args
    global RESUME
    RESUME = "resume" in args
    res = next((tuple(int(v) for v in a.split("x")) for a in args if "x" in a and a[0].isdigit()),
               (540, 960) if portrait else (960, 540))
    for n in names:
        render_segment(n, samples, res, portrait)


if __name__ == "__main__":
    main()
