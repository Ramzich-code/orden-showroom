/**
 * Turns the approved Blender outputs into web assets.  `npm run assets`
 *
 *  rooms     blender/renders/final/<room>/  ->  public/rooms/<room>/
 *            beauty + plate per camera (WebP), depth (8-bit WebP, blurred a
 *            touch for the parallax), probe.hdr (light probe for the GLB),
 *            and the camera data -> src/config/scenes/<room>.json
 *  textures  blender/assets (CC0 scans)  ->  public/textures/<key>_{color,rough,normal}.jpg
 *            colour-graded exactly like blender/products/materials.py
 *            (HueSaturation node in linear space, then tint), roughness
 *            remapped to the same finish range.
 */
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const FINAL = join(ROOT, "blender", "renders", "final");
const ASSETS = join(ROOT, "blender", "assets");
const ROOMS = ["living", "bedroom", "storage"];
// every Blender camera found (cam_room, cam_product, cam_product_<id>, and the
// 9:16 phone variants *_p) -> same slug as cameraSlug() in src/config/rooms.ts
const slug = (cam) => cam.replace(/^cam_/, "").replace(/_p$/, "-p").replace(/_/g, "-");
const IMG_W = 2048;
const TEX_W = 1024;

/* ------------------------------------------------------------------ rooms */

async function rooms() {
  mkdirSync(join(ROOT, "src", "config", "scenes"), { recursive: true });
  for (const room of ROOMS) {
    const src = join(FINAL, room);
    const out = join(ROOT, "public", "rooms", room);
    mkdirSync(out, { recursive: true });
    const cams = readdirSync(src).filter((f) => f.endsWith("_beauty.png")).map((f) => f.replace(/_beauty\.png$/, ""));
    for (const cam of cams) {
      const shot = slug(cam);
      const portrait = cam.endsWith("_p");
      for (const kind of ["beauty", "plate"]) {
        await sharp(join(src, `${cam}_${kind}.png`))
          .resize({ width: portrait ? 1080 : IMG_W, withoutEnlargement: true })
          .webp({ quality: 84, effort: 6 })
          .toFile(join(out, `${shot}-${kind}.webp`));
      }
      await sharp(join(src, `${cam}_depth.png`))
        .resize({ width: portrait ? 540 : 1024 })
        .blur(1.2)
        .toColourspace("b-w")
        .webp({ lossless: true })
        .toFile(join(out, `${shot}-depth.webp`));
    }
    for (const f of readdirSync(src).filter((f) => /^probe-.*\.hdr$/.test(f))) copyFileSync(join(src, f), join(out, f));
    const scene = JSON.parse(readFileSync(join(src, `${room}.json`), "utf8"));
    writeFileSync(join(ROOT, "src", "config", "scenes", `${room}.json`), JSON.stringify(scene, null, 2) + "\n");
    console.log("[assets] room", room);
  }
}

/* ---------------------------------------------------------------- journey */

// Scroll journey frame sequences (blender/journey/journey.py) -> public/journey/<segment>[-p]/NNN.webp
// and src/config/journey.json (frame counts per segment and orientation).
const JOURNEY = join(ROOT, "blender", "renders", "journey");
async function journey() {
  const manifest = {};
  for (const dir of readdirSync(JOURNEY, { withFileTypes: true }).filter((d) => d.isDirectory())) {
    const frames = readdirSync(join(JOURNEY, dir.name)).filter((f) => /^f_\d+\.png$/.test(f)).sort();
    if (!frames.length) continue;
    const portrait = dir.name.endsWith("-p");
    const out = join(ROOT, "public", "journey", dir.name);
    mkdirSync(out, { recursive: true });
    for (let i = 0; i < frames.length; i++) {
      await sharp(join(JOURNEY, dir.name, frames[i]))
        .resize({ width: portrait ? 720 : 1280, withoutEnlargement: true })
        .webp({ quality: 72, effort: 5 })
        .toFile(join(out, `${String(i + 1).padStart(3, "0")}.webp`));
    }
    const seg = dir.name.replace(/-p$/, "");
    manifest[seg] = { ...(manifest[seg] ?? {}), [portrait ? "portrait" : "landscape"]: frames.length };
    console.log("[assets] journey", dir.name, frames.length, "frames");
  }
  writeFileSync(join(ROOT, "src", "config", "journey.json"), `${JSON.stringify(manifest, null, 2)}\n`);
}

/* ----------------------------------------------------------------- models */

// AO atlases and floor shadow cards from export_glb.py -> WebP (smaller; alpha kept)
async function models() {
  const dir = join(ROOT, "public", "models");
  for (const f of readdirSync(dir)) {
    const m = f.match(/^(.*_(ao|shadow)).(jpg|png)$/);
    if (!m) continue;
    await sharp(join(dir, f))
      .webp(m[2] === "ao" ? { quality: 82 } : { quality: 85, alphaQuality: 90 })
      .toFile(join(dir, `${m[1]}.webp`));
    unlinkSync(join(dir, f));
    console.log("[assets] model map", `${m[1]}.webp`);
  }
}

/* --------------------------------------------------------------- textures */

// Mirrors TEX / GRADE / ROUGH in blender/products/materials.py.
const TEXTURES = {
  travertine: {
    dir: "Travertine009",
    color: "Travertine009_4K-JPG_Color.jpg",
    rough: "Travertine009_4K-JPG_Roughness.jpg",
    normal: "Travertine009_4K-JPG_NormalGL.jpg",
    grade: { hue: 0.5, sat: 0.85, val: 0.96 },
    roughRange: [0.48, 0.78],
  },
  marble: {
    dir: "Marble019",
    color: "Marble019_4K-JPG_Color.jpg",
    rough: "Marble019_4K-JPG_Roughness.jpg",
    normal: "Marble019_4K-JPG_NormalGL.jpg",
    grade: { hue: 0.5, sat: 0.85, val: 0.97, tint: [1.0, 0.98, 0.95] },
    roughRange: [0.1, 0.28],
  },
  walnut: {
    dir: "walnut_veneer",
    color: "walnut_veneer_diff_4k.jpg",
    rough: "walnut_veneer_rough_4k.jpg",
    normal: "walnut_veneer_nor_gl_4k.jpg",
    grade: { hue: 0.49, sat: 0.95, val: 0.23 },
    roughRange: [0.38, 0.62],
  },
  boucle: {
    dir: "curly_teddy_natural",
    color: "curly_teddy_natural_diff_4k.jpg",
    rough: "curly_teddy_natural_rough_4k.jpg",
    normal: "curly_teddy_natural_nor_gl_4k.jpg",
    grade: { hue: 0.5, sat: 0.35, val: 0.9, tint: [0.86, 0.77, 0.64] },   // "boucle_oat" in materials.py
    roughRange: [0.85, 1.0],
  },
  oak: {
    dir: "oak_veneer_02",
    color: "oak_veneer_02_diff_4k.jpg",
    rough: "oak_veneer_02_rough_4k.jpg",
    normal: "oak_veneer_02_nor_gl_4k.jpg",
    grade: { hue: 0.512, sat: 1.15, val: 0.74 },
    roughRange: [0.42, 0.66],
  },
};

const toLin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toSrgb = (c) => (c <= 0.0031308 ? c * 12.92 : 1.055 * c ** (1 / 2.4) - 0.055);

function rgb2hsv(r, g, b) {
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const d = max - min;
  let h = 0;
  if (d > 0) {
    if (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h /= 6;
    if (h < 0) h += 1;
  }
  return [h, max > 0 ? d / max : 0, max];
}

function hsv2rgb(h, s, v) {
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - f * s);
  const t = v * (1 - (1 - f) * s);
  return [
    [v, q, p, p, t, v][i % 6],
    [t, v, v, q, p, p][i % 6],
    [p, p, t, v, v, q][i % 6],
  ];
}

/** Blender HueSaturation node (linear), then multiply tint. */
async function gradeColor(file, grade, out) {
  const { data, info } = await sharp(file).resize({ width: TEX_W }).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const [tr, tg, tb] = grade.tint ?? [1, 1, 1];
  for (let i = 0; i < data.length; i += 3) {
    let [h, s, v] = rgb2hsv(toLin(data[i] / 255), toLin(data[i + 1] / 255), toLin(data[i + 2] / 255));
    h = (h + grade.hue - 0.5 + 1) % 1;
    s = Math.min(1, s * grade.sat);
    v = v * grade.val;
    const [r, g, b] = hsv2rgb(h, s, v);
    data[i] = Math.round(Math.min(1, toSrgb(Math.max(0, r * tr))) * 255);
    data[i + 1] = Math.round(Math.min(1, toSrgb(Math.max(0, g * tg))) * 255);
    data[i + 2] = Math.round(Math.min(1, toSrgb(Math.max(0, b * tb))) * 255);
  }
  await sharp(data, { raw: info }).jpeg({ quality: 86, mozjpeg: true }).toFile(out);
}

async function remapRough(file, [lo, hi], out) {
  const { data, info } = await sharp(file).resize({ width: TEX_W }).greyscale().raw().toBuffer({ resolveWithObject: true });
  for (let i = 0; i < data.length; i++) data[i] = Math.round((lo + (data[i] / 255) * (hi - lo)) * 255);
  await sharp(data, { raw: info }).jpeg({ quality: 86 }).toFile(out);
}

async function textures() {
  const out = join(ROOT, "public", "textures");
  mkdirSync(out, { recursive: true });
  for (const [key, t] of Object.entries(TEXTURES)) {
    const d = join(ASSETS, t.dir);
    if (!existsSync(join(d, t.color))) throw new Error(`missing source scan: ${join(d, t.color)}`);
    await gradeColor(join(d, t.color), t.grade, join(out, `${key}_color.jpg`));
    await remapRough(join(d, t.rough), t.roughRange, join(out, `${key}_rough.jpg`));
    await sharp(join(d, t.normal)).resize({ width: TEX_W }).jpeg({ quality: 90 }).toFile(join(out, `${key}_normal.jpg`));
    console.log("[assets] texture", key);
  }
}

const only = process.argv.slice(2);
if (!only.length || only.includes("rooms")) await rooms();
if (!only.length || only.includes("textures")) await textures();
if (!only.length || only.includes("models")) await models();
if (!only.length || only.includes("journey")) await journey();
