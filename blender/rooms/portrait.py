"""
Portrait (9:16) cameras for phones: same rooms, same light, framed for a
vertical screen so the product is never cropped by a 16:9 still.

    blender -b --factory-startup --python blender/rooms/portrait.py -- [living bedroom storage] [samples]

Adds cam_room_p / cam_product_p to blender/rooms/<room>.blend (re-saved; no
geometry changes) and renders 540 x 960 framing previews to
blender/renders/rooms_preview/<room>_<cam>.png. Final stills:
render_final.py -- portrait.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room_kit as rk  # noqa: E402
import rooms  # noqa: E402

# name: (location, target, lens mm). Blender fits the sensor to the long side,
# so in portrait the lens sets the vertical field of view.
PORTRAIT = {
    "living": {
        "cam_room_p": ((-2.35, -2.3, 2.0), (-0.5, 0.75, 0.02), 21),
        "cam_product_p": ((-2.05, -1.75, 1.3), (-0.6, 0.3, 0.16), 27),
    },
    "bedroom": {
        "cam_room_p": ((-0.75, -2.15, 1.3), (-0.05, 2.2, 0.55), 22),
        "cam_product_p": ((-1.05, -0.35, 1.0), (-0.32, 1.76, 0.36), 27),
    },
    "storage": {
        "cam_room_p": ((0.3, -2.05, 1.3), (-0.35, 2.2, 0.85), 19),
        "cam_product_p": ((0.75, -1.7, 1.2), (-0.38, 1.84, 0.98), 21),
    },
}
PORTRAIT_RES = (1080, 1920)


def add_cameras(room):
    """Adds (or replaces) the portrait cameras in the open room file."""
    for name, (loc, target, lens) in PORTRAIT[room].items():
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        rk.camera(name, loc, target, lens)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = [a for a in args if a in PORTRAIT] or list(PORTRAIT)
    samples = next((int(a) for a in args if a.isdigit()), 32)
    for room in names:
        path = os.path.join(HERE, f"{room}.blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        add_cameras(room)
        bpy.ops.wm.save_as_mainfile(filepath=path)
        rk.preview_settings(samples=samples, res=(540, 960), exposure=rooms.EXPOSURE[room])
        rk.render_cameras(room, [bpy.data.objects[n] for n in PORTRAIT[room]])


if __name__ == "__main__":
    main()
