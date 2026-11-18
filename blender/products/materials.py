"""
ORDEN PBR material library (Cycles), built from the approved scanned texture
sets in blender/assets/ (lot A, CC0). One material per (product, finish, role),
mirroring src/three/materials.ts so renders and website agree:

  body      follows the finish; "signature" = the product's own material
  accent    oak, or ink-black on an oak body
  travertine / marble / base / metal / interior   fixed

Every material is physically based: base colour, roughness and normal maps,
height through a bump node (no geometry change), and a very light
fingerprint/smudge layer in roughness so no surface reads as CG-perfect.
"""
import os

import bpy

ASSETS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))

TEX = {
    "travertine": dict(dir="Travertine009", color="Travertine009_4K-JPG_Color.jpg", rough="Travertine009_4K-JPG_Roughness.jpg",
                       normal="Travertine009_4K-JPG_NormalGL.jpg", height="Travertine009_4K-JPG_Displacement.jpg",
                       ao="Travertine009_4K-JPG_AmbientOcclusion.jpg", tile=1.25, rot=0.0),
    "marble": dict(dir="Marble019", color="Marble019_4K-JPG_Color.jpg", rough="Marble019_4K-JPG_Roughness.jpg",
                   normal="Marble019_4K-JPG_NormalGL.jpg", height="Marble019_4K-JPG_Displacement.jpg", tile=1.4, rot=0.35),
    # veneer scans have their grain along V: rotate 90 deg so it follows U (the length of each part)
    "walnut": dict(dir="walnut_veneer", color="walnut_veneer_diff_4k.jpg", rough="walnut_veneer_rough_4k.jpg",
                   normal="walnut_veneer_nor_gl_4k.jpg", height="walnut_veneer_disp_4k.jpg", tile=1.1, rot=1.5708),
    "oak": dict(dir="oak_veneer_02", color="oak_veneer_02_diff_4k.jpg", rough="oak_veneer_02_rough_4k.jpg",
                normal="oak_veneer_02_nor_gl_4k.jpg", height="oak_veneer_02_disp_4k.jpg", tile=1.1, rot=0.0),
}
# --- room materials (lot B); product materials above are unchanged ---------
_PH = lambda d, r: dict(dir=d, color=f"{d}_diff_{r}.jpg", rough=f"{d}_rough_{r}.jpg",
                        normal=f"{d}_nor_gl_{r}.jpg", height=f"{d}_disp_{r}.jpg")
TEX.update({
    "floor": dict(_PH("laminate_floor_02", "4k"), tile=2.0, rot=0.0),
    "plaster": dict(_PH("beige_wall_001", "4k"), tile=2.5, rot=0.0),
    "boucle": dict(_PH("curly_teddy_natural", "4k"), tile=0.45, rot=0.0),
    "linen": dict(_PH("rough_linen", "2k"), tile=0.6, rot=0.0),
    "linen_sand": dict(_PH("rough_linen", "2k"), tile=0.6, rot=0.0),
    "carpet": dict(dir="Carpet016", color="Carpet016_2K-JPG_Color.jpg", rough="Carpet016_2K-JPG_Roughness.jpg",
                   normal="Carpet016_2K-JPG_NormalGL.jpg", height="Carpet016_2K-JPG_Displacement.jpg", tile=0.8, rot=0.0),
})
TEX.update({   # tinted variants of the same scans (no extra downloads)
    "floor_dark": dict(TEX["floor"]),
    "floor_grey": dict(TEX["floor"]),
    "plaster_grey": dict(TEX["plaster"]),
    "plaster_white": dict(TEX["plaster"]),
    "linen_grey": dict(TEX["linen"]),
    "linen_cream": dict(TEX["linen"]),
    "carpet_grey": dict(TEX["carpet"]),
    "marble_warm": dict(TEX["marble"]),
    "boucle_oat": dict(TEX["boucle"], tile=0.32),
    "oak_warm": dict(TEX["oak"]),
})
FABRICS = {"boucle", "boucle_oat", "linen", "linen_sand", "carpet", "linen_grey", "linen_cream", "carpet_grey"}

SMUDGE = os.path.join(ASSETS, "Fingerprints003", "Fingerprints003_2K-JPG_Roughness.jpg")

# colour grading per scanned material, towards the approved references
GRADE = {
    "travertine": dict(hue=0.5, sat=0.85, val=0.96),   # pale warm beige, as in the reference
    "walnut": dict(hue=0.49, sat=0.95, val=0.23),      # deep chocolate walnut (reference)
    "oak": dict(hue=0.512, sat=1.15, val=0.74),        # warm honey natural oak (scan is pale and pinkish)
    "marble": dict(hue=0.5, sat=0.85, val=0.97, tint=(1.0, 0.98, 0.95)),
    "floor": dict(hue=0.505, sat=0.85, val=0.95),      # light natural oak boards
    "plaster": dict(hue=0.5, sat=0.9, val=1.05),        # warm off-white plaster
    "boucle": dict(hue=0.5, sat=0.55, val=1.12),        # cream boucle (sofa)
    "linen": dict(hue=0.5, sat=0.0, val=1.3, tint=(1.0, 0.96, 0.90)),         # off-white bedding (scan is blue: neutralised)
    "linen_sand": dict(hue=0.5, sat=0.0, val=1.35, tint=(0.62, 0.50, 0.35)),  # warm sand linen (headboard, bed base)
    "carpet": dict(hue=0.5, sat=0.7, val=1.05),         # natural wool rug
    "floor_dark": dict(hue=0.495, sat=0.9, val=0.32),   # espresso oak (bedroom reference)
    "floor_grey": dict(hue=0.5, sat=0.0, val=0.62, tint=(0.62, 0.58, 0.54)),   # warm grey floor (living reference)
    "plaster_grey": dict(hue=0.5, sat=0.0, val=1.1, tint=(0.58, 0.60, 0.61)),  # cool light grey microcement (bedroom)
    "plaster_white": dict(hue=0.5, sat=0.15, val=1.3),  # warm white (dressing)
    "linen_grey": dict(hue=0.5, sat=0.0, val=1.25, tint=(0.62, 0.58, 0.52)),   # grey-beige duvet
    "linen_cream": dict(hue=0.5, sat=0.0, val=1.35, tint=(0.88, 0.82, 0.72)),  # cream (sofa, cushions)
    "carpet_grey": dict(hue=0.5, sat=0.0, val=0.9, tint=(0.50, 0.47, 0.43)),   # taupe-grey rug (living)
    "marble_warm": dict(hue=0.5, sat=0.6, val=1.0, tint=(1.0, 0.93, 0.82)),    # cream marble panel (dressing)
    "oak_warm": dict(hue=0.505, sat=1.2, val=0.62),     # warm oak joinery (dressing niche)
    "boucle_oat": dict(hue=0.5, sat=0.35, val=0.9, tint=(0.86, 0.77, 0.64)),  # oatmeal boucle (sofa reference)
}

# roughness remap per scanned material (finish, not the scan's capture state)
ROUGH = {
    "travertine": (0.48, 0.78),   # honed, matte
    "walnut": (0.38, 0.62),       # oiled
    "oak": (0.42, 0.66),          # oiled
    "marble": (0.10, 0.28),       # polished marble-effect
    "floor": (0.32, 0.58),
    "plaster": (0.78, 0.95),
    "boucle": (0.85, 1.0),
    "linen": (0.75, 0.95),
    "linen_sand": (0.75, 0.95),
    "carpet": (0.88, 1.0),
    "floor_dark": (0.30, 0.55), "floor_grey": (0.35, 0.6), "plaster_grey": (0.75, 0.95), "plaster_white": (0.8, 0.95),
    "linen_grey": (0.75, 0.95), "linen_cream": (0.7, 0.92), "carpet_grey": (0.88, 1.0),
    "marble_warm": (0.10, 0.25), "oak_warm": (0.4, 0.62), "boucle_oat": (0.85, 1.0),
}

def _lin(srgb):
    """Principled base colour is LINEAR: convert display (sRGB) picks."""
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)


PAINT = {  # matte lacquers: display colour (sRGB) picked from the references, roughness
    "white": (_lin((0.93, 0.92, 0.90)), 0.42),
    "black": (_lin((0.13, 0.125, 0.12)), 0.38),
    "taupe": (_lin((0.66, 0.60, 0.48)), 0.48),    # warm khaki taupe (bedside reference)
    "greige": (_lin((0.84, 0.79, 0.71)), 0.45),   # warm cream greige (wardrobe reference)
}

SIGNATURE_BODY = {"coffee-table": "walnut", "bedside-table": "taupe", "wardrobe": "greige",
                  "headboard-shelf": "oak", "sofa": "oak", "shoe-bench": "oak"}

# fixed roles of the 2026-11-18 additions
FIXED_ROLE = {"fabric": "boucle_oat", "socket": "socket", "light": "light"}


def _img(path, non_color):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    return img


def _scanned(name, key):
    t = TEX[key]
    g = GRADE[key]
    d = os.path.join(ASSETS, t["dir"])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    n, L = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]

    uv = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / t["tile"], 1 / t["tile"], 1)
    mp.inputs["Rotation"].default_value = (0, 0, t["rot"])
    L.new(uv.outputs["UV"], mp.inputs["Vector"])

    def tex(file, non_color):
        node = n.new("ShaderNodeTexImage")
        node.image = _img(os.path.join(d, file), non_color)
        node.interpolation = "Cubic"
        L.new(mp.outputs["Vector"], node.inputs["Vector"])
        return node

    col = tex(t["color"], False)
    hsv = n.new("ShaderNodeHueSaturation")
    hsv.inputs["Hue"].default_value = g["hue"]
    hsv.inputs["Saturation"].default_value = g["sat"]
    hsv.inputs["Value"].default_value = g["val"]
    L.new(col.outputs["Color"], hsv.inputs["Color"])
    if "tint" in g:                       # neutralised scans recoloured to the ORDEN palette
        tint = n.new("ShaderNodeMix")
        tint.data_type = "RGBA"
        tint.blend_type = "MULTIPLY"
        tint.inputs["Factor"].default_value = 1.0
        L.new(hsv.outputs["Color"], tint.inputs["A"])
        tint.inputs["B"].default_value = (*g["tint"], 1)
        hsv = type("H", (), {"outputs": {"Color": tint.outputs["Result"]}})()
    if "ao" in t:
        ao = tex(t["ao"], True)
        mix = n.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 0.35
        L.new(hsv.outputs["Color"], mix.inputs["A"])
        L.new(ao.outputs["Color"], mix.inputs["B"])
        L.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        L.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])

    rough = tex(t["rough"], True)
    rmap = n.new("ShaderNodeMapRange")
    rmap.inputs["To Min"].default_value, rmap.inputs["To Max"].default_value = ROUGH[key]
    L.new(rough.outputs["Color"], rmap.inputs["Value"])
    L.new(_with_smudge(nt, rmap.outputs["Result"]), bsdf.inputs["Roughness"])

    nrm = tex(t["normal"], True)
    nmap = n.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 0.6
    L.new(nrm.outputs["Color"], nmap.inputs["Color"])
    hgt = tex(t["height"], True)
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.0006
    L.new(hgt.outputs["Color"], bump.inputs["Height"])
    L.new(nmap.outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    if key in FABRICS:                    # textile fibre sheen
        bsdf.inputs["Sheen Weight"].default_value = 0.5
        bsdf.inputs["Sheen Roughness"].default_value = 0.6
        nmap.inputs["Strength"].default_value = 0.9
    if key in ("walnut", "oak", "oak_warm"):   # hard-wax oil: faint satin coat
        bsdf.inputs["Coat Weight"].default_value = 0.12
        bsdf.inputs["Coat Roughness"].default_value = 0.35
    if key in ("marble", "marble_warm"):  # honed-polished marble-effect top
        bsdf.inputs["Coat Weight"].default_value = 0.35
        bsdf.inputs["Coat Roughness"].default_value = 0.08
    return m


def _with_smudge(nt, rough_socket, amount=0.12):
    """Adds a light fingerprint/smudge layer to a roughness signal."""
    n, L = nt.nodes, nt.links
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.7, 1.7, 1)
    L.new(tc.outputs["UV"], mp.inputs["Vector"])
    sm = n.new("ShaderNodeTexImage")
    sm.image = _img(SMUDGE, True)
    L.new(mp.outputs["Vector"], sm.inputs["Vector"])
    mix = n.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = amount
    L.new(rough_socket, mix.inputs["A"])
    L.new(sm.outputs["Color"], mix.inputs["B"])
    return mix.outputs["Result"]


def _paint(name, key):
    colour, rough = PAINT[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1)
    val = nt.nodes.new("ShaderNodeValue")
    val.outputs[0].default_value = rough
    nt.links.new(_with_smudge(nt, val.outputs[0], 0.06), bsdf.inputs["Roughness"])
    bsdf.inputs["Coat Weight"].default_value = 0.08
    bsdf.inputs["Coat Roughness"].default_value = 0.5
    _micro_surface(nt, bsdf, scale=650.0, strength=0.035)
    return m


def _micro_surface(nt, bsdf, scale=500.0, strength=0.04):
    """Very fine surface breakup (lacquer orange-peel / fabric grain) on the
    normal, so even plain colours catch light like real material."""
    n, L = nt.nodes, nt.links
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.0005
    L.new(noise.outputs["Fac"], bump.inputs["Height"])
    if bsdf.inputs["Normal"].is_linked:
        L.new(bsdf.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _plain(name, colour, rough, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


_cache = {}


def material(key):
    if key in _cache:
        return _cache[key]
    if key in TEX:
        m = _scanned(f"orden_{key}", key)
    elif key in PAINT:
        m = _paint(f"orden_{key}", key)
    elif key == "base":
        m = _plain("orden_base", (0.018, 0.016, 0.015), 0.5)
    elif key == "metal":
        m = _plain("orden_metal", (0.62, 0.60, 0.57), 0.3, 1.0)
    elif key == "socket":
        m = _plain("orden_socket", (0.028, 0.028, 0.03), 0.42)
    elif key == "light":
        m = _plain("orden_light", (0.95, 0.9, 0.82), 0.3)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Color"].default_value = (1.0, 0.72, 0.42, 1)
        b.inputs["Emission Strength"].default_value = 12.0
    elif key == "interior":
        m = _plain("orden_interior", (0.62, 0.52, 0.38), 0.65)
    else:
        raise KeyError(key)
    _cache[key] = m
    return m


def resolve(product, finish, role):
    """Same mapping as the website (src/three/materials.ts)."""
    if role == "body":
        return SIGNATURE_BODY[product] if finish == "signature" else finish
    if role == "accent":   # pulls: walnut in Signature (as in the approved image)
        return "walnut" if finish == "signature" else ("black" if finish == "oak" else "oak")
    return FIXED_ROLE.get(role, role)


def apply_finish(root, product, finish):
    for o in root.children:
        if o.type == "MESH" and "role" in o:
            o.data.materials.clear()
            o.data.materials.append(material(resolve(product, finish, o["role"])))
