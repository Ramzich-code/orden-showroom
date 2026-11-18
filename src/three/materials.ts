import * as THREE from "three";
import type { FinishId, MaterialRole, Product } from "@/config/products";

/**
 * Real-time materials, matched to the Cycles materials in
 * blender/products/materials.py (same CC0 scans, same colour grading baked
 * into public/textures by `npm run assets`, same lacquer colours, same UV
 * tiling). A component's role decides how it reacts to a finish:
 *   body    the finish; Signature = the product's own material
 *   accent  pulls and legs: walnut in Signature, black on oak, oak otherwise
 *   others  fixed (travertine, marble, base, metal, interior)
 */
export type MaterialKey =
  | "walnut"
  | "oak"
  | "travertine"
  | "marble"
  | "white"
  | "black"
  | "taupe"
  | "greige"
  | "base"
  | "metal"
  | "interior";

type Scanned = "walnut" | "oak" | "travertine" | "marble";

/** Blender Mapping node: scale 1/tile, rotation about the UV origin. */
const SCAN: Record<Scanned, { tile: number; rot: number; normal: number }> = {
  travertine: { tile: 1.25, rot: 0, normal: 0.6 },
  marble: { tile: 1.4, rot: 0.35, normal: 0.3 },
  walnut: { tile: 1.1, rot: Math.PI / 2, normal: 0.5 },
  oak: { tile: 1.1, rot: 0, normal: 0.5 },
};

/** Matte lacquers: display colour picked from the references, roughness. */
const PAINT: Record<"white" | "black" | "taupe" | "greige", { srgb: [number, number, number]; roughness: number }> = {
  white: { srgb: [0.93, 0.92, 0.9], roughness: 0.42 },
  black: { srgb: [0.13, 0.125, 0.12], roughness: 0.38 },
  taupe: { srgb: [0.66, 0.6, 0.48], roughness: 0.48 },
  greige: { srgb: [0.84, 0.79, 0.71], roughness: 0.45 },
};

const loader = new THREE.TextureLoader();
const textures = new Map<string, THREE.Texture>();

function scanTexture(key: Scanned, map: "color" | "rough" | "normal") {
  const url = `/textures/${key}_${map}.jpg`;
  let t = textures.get(url);
  if (!t) {
    t = loader.load(url);
    t.colorSpace = map === "color" ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.setScalar(1 / SCAN[key].tile);
    t.rotation = -SCAN[key].rot;
    t.anisotropy = 8;
    textures.set(url, t);
  }
  return t;
}

let lacquerBump: THREE.Texture | null = null;
/** Very fine orange-peel, like the micro-surface on the Cycles lacquers. */
function lacquerNoise() {
  if (lacquerBump) return lacquerBump;
  const size = 256;
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const ctx = c.getContext("2d")!;
  const img = ctx.createImageData(size, size);
  let s = 1234567;
  for (let i = 0; i < size * size; i++) {
    s = (s * 16807) % 2147483647;
    const v = 118 + ((s / 2147483647) * 20) | 0;
    img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v;
    img.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  lacquerBump = new THREE.CanvasTexture(c);
  lacquerBump.wrapS = lacquerBump.wrapT = THREE.RepeatWrapping;
  lacquerBump.repeat.setScalar(6);
  return lacquerBump;
}

function make(key: MaterialKey): THREE.Material {
  switch (key) {
    case "walnut":
    case "oak":
    case "travertine":
    case "marble": {
      const m = new THREE.MeshPhysicalMaterial({
        map: scanTexture(key, "color"),
        roughnessMap: scanTexture(key, "rough"),
        roughness: 1,
        normalMap: scanTexture(key, "normal"),
        normalScale: new THREE.Vector2(SCAN[key].normal, SCAN[key].normal),
      });
      if (key === "marble") {
        m.clearcoat = 0.5;
        m.clearcoatRoughness = 0.12;
      } else if (key === "walnut" || key === "oak") {
        m.clearcoat = 0.12;
        m.clearcoatRoughness = 0.45;
      }
      return m;
    }
    case "white":
    case "black":
    case "taupe":
    case "greige": {
      const p = PAINT[key];
      return new THREE.MeshPhysicalMaterial({
        color: new THREE.Color().setRGB(...p.srgb, THREE.SRGBColorSpace),
        roughness: p.roughness,
        clearcoat: 0.08,
        clearcoatRoughness: 0.5,
        bumpMap: lacquerNoise(),
        bumpScale: 0.12,
      });
    }
    case "base":
      return new THREE.MeshStandardMaterial({ color: new THREE.Color(0.018, 0.016, 0.015), roughness: 0.5 });
    case "metal":
      return new THREE.MeshStandardMaterial({ color: new THREE.Color(0.62, 0.6, 0.57), metalness: 1, roughness: 0.3 });
    case "interior":
      return new THREE.MeshStandardMaterial({ color: new THREE.Color(0.62, 0.52, 0.38), roughness: 0.65 });
  }
}

const library = new Map<MaterialKey, THREE.Material>();

export function getMaterialByKey(key: MaterialKey): THREE.Material {
  let m = library.get(key);
  if (!m) {
    m = make(key);
    library.set(key, m);
  }
  return m;
}

/** Same mapping as resolve() in blender/products/materials.py. */
export function resolveMaterialKey(product: Product, finish: FinishId, role: MaterialRole): MaterialKey {
  switch (role) {
    case "body":
      return finish === "signature" ? product.signature.body : finish;
    case "accent":
      return finish === "signature" ? "walnut" : finish === "oak" ? "black" : "oak";
    default:
      return role;
  }
}

/** Ambient occlusion baked in Cycles (public/models/<id>_ao.webp, on the GLB's second UV set). */
function aoTexture(product: Product) {
  const url = product.model.replace(/\.glb$/, "_ao.webp");
  let t = textures.get(url);
  if (!t) {
    t = loader.load(url);
    t.colorSpace = THREE.NoColorSpace;
    t.channel = 1;
    t.flipY = false; // glTF UV convention
    // no mipmaps: they bleed across the atlas islands and draw dark seams
    t.generateMipmaps = false;
    t.minFilter = THREE.LinearFilter;
    textures.set(url, t);
  }
  return t;
}

const perProduct = new Map<string, THREE.Material>();

/** The shared material for this role and finish, with the product's own AO. */
export function getMaterial(product: Product, finish: FinishId, role: MaterialRole): THREE.Material {
  const key = resolveMaterialKey(product, finish, role);
  const id = `${product.id}:${key}`;
  let m = perProduct.get(id);
  if (!m) {
    m = getMaterialByKey(key).clone() as THREE.MeshStandardMaterial;
    (m as THREE.MeshStandardMaterial).aoMap = aoTexture(product);
    (m as THREE.MeshStandardMaterial).aoMapIntensity = 0.85;
    perProduct.set(id, m);
  }
  return m;
}

/** Starts the texture downloads early (used while the loader is up). */
export function preloadMaterials() {
  (["walnut", "oak", "travertine", "marble"] as const).forEach((k) => getMaterialByKey(k));
}
