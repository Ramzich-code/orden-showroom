/**
 * Procedural canvas textures. Generated once on the client and cached, so the
 * showroom ships no image assets. Swap any of these for real scanned textures
 * (KTX2/JPG) by returning a loaded texture instead.
 */
import * as THREE from "three";

const cache = new Map<string, THREE.Texture>();

function memo<T extends THREE.Texture>(key: string, make: () => T): T {
  const hit = cache.get(key);
  if (hit) return hit as T;
  const tex = make();
  cache.set(key, tex);
  return tex;
}

/** Deterministic PRNG so textures look the same on every load. */
export function rng(seed: number) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function canvas(w: number, h: number) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;
  return { c, ctx };
}

function finalize(c: HTMLCanvasElement, srgb = true, repeat: [number, number] = [1, 1]) {
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  t.anisotropy = 8;
  t.needsUpdate = true;
  return t;
}

function grain(
  ctx: CanvasRenderingContext2D,
  x0: number,
  y0: number,
  w: number,
  h: number,
  r: () => number,
  density: number,
  palette: { dark: string; light: string } = { dark: "92, 60, 32", light: "255, 236, 205" },
) {
  const lines = Math.floor(h * density);
  for (let i = 0; i < lines; i++) {
    const y = y0 + r() * h;
    const amp = 1 + r() * 3.5;
    const freq = 0.004 + r() * 0.01;
    const phase = r() * Math.PI * 2;
    const dark = r() > 0.35;
    ctx.strokeStyle = dark
      ? `rgba(${palette.dark}, ${0.05 + r() * 0.16})`
      : `rgba(${palette.light}, ${0.04 + r() * 0.1})`;
    ctx.lineWidth = 0.4 + r() * 1.8;
    ctx.beginPath();
    for (let x = x0; x <= x0 + w; x += 6) {
      const yy = y + Math.sin(x * freq + phase) * amp + Math.sin(x * freq * 3.1 + phase) * amp * 0.25;
      if (x === x0) ctx.moveTo(x, yy);
      else ctx.lineTo(x, yy);
    }
    ctx.stroke();
  }
}

/** Oak board, grain running along U. */
export function oakTexture() {
  return memo("oak", () => {
    const { c, ctx } = canvas(1024, 512);
    const r = rng(11);
    const g = ctx.createLinearGradient(0, 0, 0, 512);
    g.addColorStop(0, "#C89F72");
    g.addColorStop(0.5, "#C2966A");
    g.addColorStop(1, "#C9A276");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 1024, 512);
    grain(ctx, 0, 0, 1024, 512, r, 0.45);
    // medullary ray flecks, typical of quarter-sawn oak
    for (let i = 0; i < 140; i++) {
      ctx.fillStyle = `rgba(240, 214, 176, ${0.08 + r() * 0.12})`;
      ctx.beginPath();
      ctx.ellipse(r() * 1024, r() * 512, 4 + r() * 14, 0.6 + r() * 1.2, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    return finalize(c);
  });
}

/** Wide oak floor planks. One tile = 1 m × 1 m, five planks wide. */
export function floorTexture() {
  return memo("floor", () => {
    const S = 1024;
    const { c, ctx } = canvas(S, S);
    const r = rng(7);
    const rows = 5;
    const rh = S / rows;
    for (let row = 0; row < rows; row++) {
      let x = -r() * S * 0.6;
      while (x < S) {
        const len = S * (0.55 + r() * 0.7);
        const tone = 0.9 + r() * 0.16;
        const base = [200 * tone, 170 * tone, 133 * tone].map((v) => Math.min(255, v | 0));
        ctx.fillStyle = `rgb(${base.join(",")})`;
        ctx.fillRect(x, row * rh, len, rh);
        ctx.save();
        ctx.beginPath();
        ctx.rect(x, row * rh, len, rh);
        ctx.clip();
        grain(ctx, x, row * rh, len, rh, r, 0.5);
        ctx.restore();
        // end joint
        ctx.fillStyle = "rgba(70, 46, 24, 0.45)";
        ctx.fillRect(x + len - 1, row * rh, 1.5, rh);
        x += len;
      }
      ctx.fillStyle = "rgba(70, 46, 24, 0.5)";
      ctx.fillRect(0, row * rh, S, 1.5);
    }
    return finalize(c);
  });
}

/** Greyscale value noise, used for bump/roughness on plaster, wool and fabric. */
export function noiseTexture(key: string, size = 256, contrast = 1, repeat: [number, number] = [1, 1]) {
  return memo(`noise:${key}`, () => {
    const { c, ctx } = canvas(size, size);
    const img = ctx.createImageData(size, size);
    const r = rng(key.length * 97 + size);
    for (let i = 0; i < size * size; i++) {
      const v = 128 + (r() - 0.5) * 255 * contrast;
      img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = Math.max(0, Math.min(255, v));
      img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    return finalize(c, false, repeat);
  });
}

/** Soft daylight seen through the window. */
export function skyTexture() {
  return memo("sky", () => {
    const { c, ctx } = canvas(512, 512);
    const g = ctx.createLinearGradient(0, 0, 0, 512);
    g.addColorStop(0, "#EEEEE8");
    g.addColorStop(0.55, "#F8F3E6");
    g.addColorStop(0.8, "#E6E2D2");
    g.addColorStop(1, "#C6CBB8");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 512, 512);
    // out-of-focus garden: soft foliage masses low in the frame
    const r = rng(5);
    ctx.filter = "blur(18px)";
    for (let i = 0; i < 26; i++) {
      const x = r() * 512;
      const y = 330 + r() * 200;
      ctx.fillStyle = `rgba(${120 + r() * 30}, ${135 + r() * 25}, ${110 + r() * 20}, ${0.25 + r() * 0.3})`;
      ctx.beginPath();
      ctx.arc(x, y, 30 + r() * 60, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.filter = "none";
    return finalize(c);
  });
}

/** Original abstract prints for the wall frames. */
export function artTexture(variant: 0 | 1) {
  return memo(`art:${variant}`, () => {
    const W = 512;
    const H = 680;
    const { c, ctx } = canvas(W, H);
    ctx.fillStyle = "#EFE9DE";
    ctx.fillRect(0, 0, W, H);
    if (variant === 0) {
      ctx.fillStyle = "#B9774E";
      ctx.beginPath();
      ctx.moveTo(130, 560);
      ctx.lineTo(130, 330);
      ctx.arc(256, 330, 126, Math.PI, 0);
      ctx.lineTo(382, 560);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#2B2926";
      ctx.beginPath();
      ctx.arc(330, 190, 46, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillStyle = "#D7C7AE";
      ctx.fillRect(96, 120, 320, 440);
      ctx.strokeStyle = "#2B2926";
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.moveTo(96, 400);
      ctx.bezierCurveTo(200, 300, 300, 470, 416, 360);
      ctx.stroke();
      ctx.fillStyle = "#8E9682";
      ctx.beginPath();
      ctx.arc(256, 250, 70, 0, Math.PI * 2);
      ctx.fill();
    }
    return finalize(c);
  });
}

/* ------------------------------------------------------- Signature materials */

/** Dark walnut, grain along U. */
export function walnutTexture() {
  return memo("walnut", () => {
    const { c, ctx } = canvas(1024, 512);
    const r = rng(23);
    const g = ctx.createLinearGradient(0, 0, 0, 512);
    g.addColorStop(0, "#4E3322");
    g.addColorStop(0.45, "#5A3B27");
    g.addColorStop(1, "#4A3020");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 1024, 512);
    // broad figure
    for (let i = 0; i < 14; i++) {
      ctx.fillStyle = `rgba(${r() > 0.5 ? "120, 82, 54" : "34, 20, 12"}, ${0.08 + r() * 0.1})`;
      ctx.fillRect(0, r() * 512, 1024, 10 + r() * 40);
    }
    grain(ctx, 0, 0, 1024, 512, r, 0.6, { dark: "28, 16, 9", light: "150, 108, 74" });
    return finalize(c);
  });
}

/** Honed travertine: soft cream bedding lines and small elongated pores. */
export function travertineTexture() {
  return memo("travertine", () => {
    const S = 1024;
    const { c, ctx } = canvas(S, S);
    const r = rng(31);
    ctx.fillStyle = "#DED4C3";
    ctx.fillRect(0, 0, S, S);
    // fine bedding
    ctx.filter = "blur(2.5px)";
    for (let i = 0; i < 150; i++) {
      const y = r() * S;
      const light = r() > 0.5;
      ctx.strokeStyle = light ? `rgba(244, 238, 226, ${0.08 + r() * 0.16})` : `rgba(182, 164, 136, ${0.06 + r() * 0.12})`;
      ctx.lineWidth = 1 + r() * 7;
      ctx.beginPath();
      const amp = 1 + r() * 4;
      const f = 0.002 + r() * 0.005;
      const ph = r() * 6.28;
      for (let x = -20; x <= S + 20; x += 16) {
        const yy = y + Math.sin(x * f + ph) * amp;
        if (x === -20) ctx.moveTo(x, yy);
        else ctx.lineTo(x, yy);
      }
      ctx.stroke();
    }
    ctx.filter = "none";
    // pores, stretched along the bedding
    for (let i = 0; i < 380; i++) {
      const len = 1.5 + r() * (r() > 0.92 ? 18 : 6);
      ctx.fillStyle = `rgba(170, 152, 124, ${0.18 + r() * 0.3})`;
      ctx.beginPath();
      ctx.ellipse(r() * S, r() * S, len, 0.5 + r() * 1.1, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    for (let i = 0; i < 5000; i++) {
      ctx.fillStyle = `rgba(${r() > 0.5 ? "255,250,242" : "160,142,114"}, ${0.04 + r() * 0.06})`;
      ctx.fillRect(r() * S, r() * S, 1.5, 1.5);
    }
    return finalize(c, true, [1.4, 1.4]);
  });
}

/** Polished white marble-effect: faint clouding and a few soft grey veins. */
export function marbleTexture() {
  return memo("marble", () => {
    const S = 1024;
    const { c, ctx } = canvas(S, S);
    const r = rng(57);
    ctx.fillStyle = "#F0EFEC";
    ctx.fillRect(0, 0, S, S);
    ctx.filter = "blur(50px)";
    for (let i = 0; i < 26; i++) {
      ctx.fillStyle = `rgba(${r() > 0.5 ? "222, 220, 216" : "252, 251, 249"}, 0.55)`;
      ctx.beginPath();
      ctx.arc(r() * S, r() * S, 80 + r() * 180, 0, Math.PI * 2);
      ctx.fill();
    }
    // Build vein polylines first (gentle random walks, rare branches), then paint them.
    const veins: { pts: [number, number][]; w: number }[] = [];
    const walk = (x: number, y: number, a: number, w: number, steps: number, depth: number) => {
      const pts: [number, number][] = [[x, y]];
      for (let s = 0; s < steps; s++) {
        a += (r() - 0.5) * 0.22;
        x += Math.cos(a) * 12;
        y += Math.sin(a) * 12;
        pts.push([x, y]);
        if (depth < 1 && r() > 0.975) walk(x, y, a + (r() > 0.5 ? 0.6 : -0.6), w * 0.5, steps * 0.35, depth + 1);
      }
      veins.push({ pts, w });
    };
    for (let i = 0; i < 4; i++) walk(-30, r() * S, -0.5 + r() * 0.5, 1.2 + r() * 1.6, 100, 0);
    const paint = (blur: number, alpha: number, widthScale: number) => {
      ctx.filter = `blur(${blur}px)`;
      ctx.strokeStyle = `rgba(128, 126, 122, ${alpha})`;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      for (const v of veins) {
        ctx.lineWidth = v.w * widthScale;
        ctx.beginPath();
        v.pts.forEach(([x, y], k) => (k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
        ctx.stroke();
      }
    };
    paint(8, 0.16, 7); // soft halo
    paint(1, 0.42, 1); // crisp core
    ctx.filter = "none";
    return finalize(c, true, [0.9, 0.9]);
  });
}
