"""
Export the approved products to real-time GLBs for the website.

    blender -b --factory-startup --python blender/products/export_glb.py -- [coffee-table bedside-table wardrobe]

Reads blender/products/<id>.blend (approved geometry, never re-saved) and writes
  public/models/<id>.glb     Y-up, one node per component named exactly like
                             the component ids in src/config/products.ts, UVs
                             and normals kept, no materials (the website
                             assigns them from each component's role, exported
                             as glTF extras "role"). A second UV set (TEXCOORD_1)
                             carries the ambient-occlusion atlas.
  public/models/<id>_ao.jpg  ambient occlusion baked in Cycles (product on a
                             floor), so the live product keeps the contact
                             darkening of the stills (gaps, undersides, joints).
"""
import json
import math
import os
import sys
import tempfile

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "public", "models"))
PRODUCTS = ["coffee-table", "bedside-table", "wardrobe"]
AO_SIZE = {"coffee-table": 2048, "bedside-table": 1024, "wardrobe": 2048}


def gpu(scene, samples):
    """Bakes run on the CPU: Cycles 4.5 + OptiX crashes baking these meshes."""
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    return
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type != "CPU"
    scene.cycles.device = "GPU"
    scene.cycles.samples = samples


def bake_ao(pid, meshes):
    scene = bpy.context.scene
    gpu(scene, 256)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("bake")
    scene.world.light_settings.distance = 0.35          # local contact occlusion only

    # floor under the product (not exported)
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    floor = bpy.context.active_object

    # shared lightmap UV ("ao", second UV set; the box UVs stay first for the scans)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        render_uv = o.data.uv_layers[0]
        ao = o.data.uv_layers.new(name="ao")
        o.data.uv_layers.active = ao
        render_uv.active_render = True
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.mode_set(mode="EDIT")              # multi-object edit: one shared atlas
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.02, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    # Cycles crashes baking meshes fresh out of a multi-object UV edit: reload
    # them from a temporary copy first (the approved .blend is not touched).
    tmp = os.path.join(tempfile.gettempdir(), f"orden_{pid}_bake.blend")
    bpy.ops.wm.save_as_mainfile(filepath=tmp, copy=True)
    bpy.ops.wm.open_mainfile(filepath=tmp)
    scene = bpy.context.scene
    gpu(scene, 256)
    scene.world.light_settings.distance = 0.35
    floor = next(o for o in bpy.data.objects if o.name.startswith("Plane"))
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and o is not floor]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]

    # white background: anything sampled outside an island reads "unoccluded", never a dark seam
    img = bpy.data.images.new(f"{pid}_ao", AO_SIZE[pid], AO_SIZE[pid], alpha=False)
    img.generated_color = (1, 1, 1, 1)
    img.colorspace_settings.name = "Non-Color"
    bake_mat = bpy.data.materials.new("bake_ao")
    bake_mat.use_nodes = True
    node = bake_mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    bake_mat.node_tree.nodes.active = node
    saved = {}
    for o in meshes:
        saved[o.name] = list(o.data.materials)
        o.data.materials.clear()
        o.data.materials.append(bake_mat)
    bpy.ops.object.bake(type="AO", margin=24, use_selected_to_active=False)

    path = os.path.join(OUT, f"{pid}_ao.jpg")
    img.filepath_raw = path
    img.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    img.save()
    for o in meshes:
        o.data.materials.clear()
        for m in saved[o.name]:
            o.data.materials.append(m)
    print(f"[ORDEN] {pid}: AO baked -> {path}")
    bpy.data.objects.remove(floor, do_unlink=True)


def bake_shadow_card(pid):
    """Occlusion the product casts on the floor, as a transparent card:
    public/models/<id>_shadow.png (black, alpha = occlusion) + its size in
    metres in public/models/<id>_shadow.json. Drawn under the live product.
    Runs on a freshly opened file (a second bake in the same session crashes
    Cycles after the multi-object UV edit)."""
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, f"{pid}.blend"))
    scene = bpy.context.scene
    gpu(scene, 256)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("bake")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    floor = bpy.context.active_object
    lo = [min((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(2)]
    hi = [max((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(2)]
    margin = 0.45
    sx, sy = hi[0] - lo[0] + 2 * margin, hi[1] - lo[1] + 2 * margin
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    floor.scale = (sx / 6, sy / 6, 1)
    floor.location = (cx, cy, 0)
    bpy.context.view_layer.update()
    res = 512
    img = bpy.data.images.new(f"{pid}_shadow_ao", res, res, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    mat = bpy.data.materials.new("bake_floor")
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    mat.node_tree.nodes.active = node
    floor.data.materials.clear()
    floor.data.materials.append(mat)
    bpy.context.scene.world.light_settings.distance = 0.6
    bpy.ops.object.select_all(action="DESELECT")
    floor.select_set(True)
    bpy.context.view_layer.objects.active = floor
    bpy.ops.object.bake(type="AO", margin=4, use_selected_to_active=False)
    ao = np.array(img.pixels[:], dtype=np.float32).reshape(res, res, 4)[:, :, 0]
    alpha = np.clip((1.0 - ao) * 1.15, 0, 1) ** 1.1
    out = bpy.data.images.new(f"{pid}_shadow", res, res, alpha=True)
    rgba = np.zeros((res, res, 4), dtype=np.float32)
    rgba[:, :, 3] = alpha
    out.pixels = rgba.ravel()
    path = os.path.join(OUT, f"{pid}_shadow.png")
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    # card in three.js units (Y-up): centre and size on the floor, product-local
    with open(os.path.join(OUT, f"{pid}_shadow.json"), "w") as f:
        json.dump({"center": [round(cx, 4), round(-cy, 4)], "size": [round(sx, 4), round(sy, 4)]}, f)
    print(f"[ORDEN] {pid}: floor shadow card -> {path}  (npm run assets converts both maps to WebP)")


def export(pid):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, f"{pid}.blend"))
    os.makedirs(OUT, exist_ok=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    bake_ao(pid, meshes)
    path = os.path.join(OUT, f"{pid}.glb")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_extras=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="NONE",
        export_cameras=False,
        export_lights=False,
        export_animations=False,
    )
    print(f"[ORDEN] {pid}: {os.path.getsize(path) / 1024:.0f} KB -> {path}")
    bake_shadow_card(pid)
    # the approved .blend is never saved from here


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for pid in [a for a in args if a in PRODUCTS] or PRODUCTS:
        export(pid)
