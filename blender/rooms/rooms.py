"""
ORDEN: three independent room scenes, one product each, after the client's
reference images (bedroom, dressing) and the coffee-table photograph (living).

    blender -b --factory-startup --python blender/rooms/rooms.py -- [living bedroom storage] [samples]

Each room is saved as blender/rooms/<room>.blend with two cameras:
  cam_room     establishing view (the website's room view)
  cam_product  product framing (website product focus)
Preview renders: blender/renders/rooms_preview/<room>_<camera>.png

"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room_kit as rk  # noqa: E402
import room_props as rp  # noqa: E402


def living():
    """SCENE 01 — Living room, staged like the coffee-table photograph: the
    Mjuk boucle sofa against the walnut panel wall, light natural rug, the Lune
    coffee table in front."""
    col = rk.new_scene()
    W, D, H = 6.4, 5.0, 2.8
    win = dict(side="right", y0=-1.6, y1=2.0, z0=0.02, z1=H - 0.02)
    rk.shell(col, W, D, H, window=win, floor="floor_grey")
    rk.daylight(sun_rot_deg=(56, 0, 66), sun_strength=3.0, hdri_strength=1.1, hdri_rot=-90)
    rk.window_fill(W, win, energy=380)
    rk.ceiling_bounce(W, D, H, energy=60)
    rp.panel_wall(col, -W / 2, 1.6, 0.0, H, D / 2)
    sofa_y = D / 2 - 0.08 - rk.bp.SOFA["D"] / 2       # 8 cm off the panel wall
    rk.place_product("sofa", (-0.55, sofa_y, 0))
    rk.rug(col, (4.0, 3.0), (-0.45, 0.8))            # natural cream wool: separates sofa, rug and table
    rk.place_product("coffee-table", (-0.6, 0.3, 0))
    top_z = rk.bp.coffee_top_z()
    rk.import_gltf("ceramic_vase_02/ceramic_vase_02_2k.gltf", (-0.78, 0.45, top_z), 1.0, 0.3, "decor_vase")
    rp.table_styling(col, top_z, -0.6, 0.3)
    cams = [rk.camera("cam_room", (-2.35, -2.3, 1.75), (-0.45, 0.95, 0.35), 30),
            rk.camera("cam_product", (-2.45, -1.75, 1.45), (-0.6, 0.3, 0.12), 36),
            rk.camera("cam_product_sofa", (0.75, -1.05, 1.7), (-0.55, sofa_y, 0.42), 30)]
    return cams


def bedroom(bedside_dims=None):
    """SCENE 02 — Bedroom after the reference: grey microcement, espresso floor,
    full-height glazing with sheers, wide channel headboard with LED wash,
    layered linen bed, pendant over the Hvile bedside table, framed art."""
    saved = dict(rk.bp.BEDSIDE)
    if bedside_dims:                                   # comparison variant only
        rk.bp.BEDSIDE.update(bedside_dims)
    try:
        col = rk.new_scene()
        W, D, H = 4.6, 4.4, 2.7
        yw = D / 2
        win = dict(side="left", y0=-1.8, y1=2.0, z0=0.02, z1=H - 0.02)
        rk.shell(col, W, D, H, window=win, wall="plaster_grey", floor="floor_dark")
        rk.daylight(sun_rot_deg=(66, 0, -70), sun_strength=1.6, hdri_strength=1.3, hdri_rot=90)
        rk.window_fill(W, win, energy=260)
        rk.ceiling_bounce(W, D, H, energy=35)
        rp.sheer_curtain(col, -W / 2 + 0.14, -1.0, 2.1, H - 0.04)
        rp.channel_headboard(col, -1.55, W / 2 - 0.02, yw, height=1.15)
        shelf_d = rk.bp.HEADBOARD_SHELF["D"]
        rk.place_product("headboard-shelf", (1.0, yw - shelf_d / 2 - 0.002, 0))   # its LEDs wash the wall
        rp.luxe_bed(col, (1.0, yw - 0.15 - 1.05, 0))
        bw, bd = rk.bp.BEDSIDE["W"], rk.bp.BEDSIDE["D"]
        bedside_y = yw - 0.15 - bd / 2 - 0.01
        bedside_x = 1.0 - 0.99 - 0.10 - bw / 2         # 10 cm clear of the duvet (bed half-width with overhang 0.99)
        rk.place_product("bedside-table", (bedside_x, bedside_y, 0))
        rp.bedside_styling(col, bedside_x - bw / 2 + 0.12, bedside_y + 0.03, rk.bp.BEDSIDE["marble_z1"])
        rp.pendant(col, bedside_x + 0.05, bedside_y - 0.05, 1.22, ceiling=H)
        rp.art_frame(col, 1.55, 1.88, 1.45, 0.95, yw, mat="travertine")
        rk.rug(col, (2.2, 2.8), (-0.35, 0.55))
        cams = [rk.camera("cam_room", (-1.15, -1.95, 1.2), (0.3, yw, 0.95), 28),
                rk.camera("cam_product", (-1.25, -0.35, 1.1), (bedside_x + 0.25, bedside_y, 0.36), 32),
                rk.camera("cam_product_headboard-shelf", (0.2, 0.55, 1.85), (1.0, yw - 0.08, 1.12), 26)]
        return cams
    finally:
        rk.bp.BEDSIDE.clear()
        rk.bp.BEDSIDE.update(saved)


def storage():
    """SCENE 03 — Dressing room around ONE standalone Fjell wardrobe (not built
    in): it stands free, slightly off the wall, with space on both sides. Around
    it: marble panel with vanity and lit round mirror, pouf, leaning floor
    mirror, the Sko shoe bench on a striped rug, linear ceiling lights, sheers."""
    col = rk.new_scene()
    W, D, H = 5.2, 4.4, 2.7
    yw = D / 2
    win = dict(side="right", y0=-1.2, y1=1.4, z0=0.02, z1=H - 0.02)
    rk.shell(col, W, D, H, window=win, wall="plaster_white", floor="floor")
    rk.daylight(sun_rot_deg=(60, 0, 64), sun_strength=3.0, hdri_strength=1.4, hdri_rot=-90)
    rk.window_fill(W, win, energy=360)
    rk.ceiling_bounce(W, D, H, energy=55)
    rp.sheer_curtain(col, W / 2 - 0.14, -1.0, 1.6, H - 0.04)
    wd = rk.bp.WARDROBE["D"]
    fx, fy = -0.45, yw - wd / 2 - 0.06                # free-standing, 6 cm off the wall
    rk.place_product("wardrobe", (fx, fy, 0))
    rk.hard_box("prop_marble_panel", (1.05, 0.02, H), (1.6, yw - 0.01, H / 2), "marble_warm", col)
    rp.vanity(col, 1.12, 2.08, yw - 0.02)
    rp.round_mirror(col, 1.6, yw - 0.02, 1.4, 0.28)
    rp.pouf(col, (1.6, 1.35, 0))
    rk.floor_mirror(col, (-1.85, yw - 0.05, 0), w=0.6, h=1.7)
    rp.striped_rug(col, (2.6, 1.6), (-0.45, 0.55))
    rk.place_product("shoe-bench", (-1.6, 0.35, 0), rot_z=1.5708)    # to the side, bays facing the room
    rp.ceiling_slots(col, [(-1.6, -0.4), (0.9, 2.0)], 0.6, H)
    cams = [rk.camera("cam_room", (0.55, -2.05, 1.35), (-0.1, yw, 1.05), 26),
            rk.camera("cam_product", (1.55, -1.05, 1.2), (fx + 0.05, fy, 0.98), 28),
            rk.camera("cam_product_shoe-bench", (0.45, -1.25, 1.15), (-1.6, 0.35, 0.25), 30)]
    return cams


ROOMS = {
    "living": living,
    "bedroom": bedroom,
    "storage": storage,
}
EXPOSURE = {"living": 0.7, "bedroom": 0.85, "storage": 0.75}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rooms = [a for a in args if a in ROOMS] or ["living", "bedroom", "storage"]
    samples = next((int(a) for a in args if a.isdigit()), 64)
    for room in rooms:
        cams = ROOMS[room]()
        rk.preview_settings(samples=samples, exposure=EXPOSURE[room])
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{room}.blend"))
        rk.render_cameras(room, cams)


if __name__ == "__main__":
    main()
