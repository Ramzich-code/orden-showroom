# ORDEN — 3D Showroom

Furniture showroom for ORDEN, Furniture & Objects. Hybrid pipeline: the three rooms are Cycles renders (Blender), the products are real-time GLBs drawn over them. Next.js 16 (App Router), TypeScript, Tailwind v4, three.js, React Three Fiber, drei, GSAP, zustand.

## Run

```bash
npm install
cp .env.example .env.local   # then set NEXT_PUBLIC_WHATSAPP_NUMBER (ordering stays disabled until it is set)
npm run dev
```

## How a room works

Each room (`living`, `bedroom`, `storage` = Dressing) holds several products (living: Lune coffee table + Mjuk sofa; bedroom: Hvile bedside table + Lys headboard shelf; dressing: Fjell wardrobe + Sko shoe bench). Every room has one room camera and one camera per product. For each camera, Cycles renders:

- **beauty**: the still with every product in place, shown by default;
- **plate**: the same view without any of the room's products (and their styling), over which all the live GLBs are drawn;
- **depth**: used for a small parallax that matches a real camera shift, so the stills and the GLB stay registered.

Phones held upright get a second set of stills rendered at 9:16, so the product is never cropped by a 16:9 image. The website camera is always exactly one of the Blender cameras (`src/config/scenes/<room>.json`). Zoom crops the frame instead of moving the camera. Each live product is lit by a Cycles light probe taken where it stands (`probe-<id>.hdr`). It also carries ambient occlusion and a floor shadow baked in Cycles.

## Asset pipeline (Blender 4.5, run from the project root)

| Step | Command | Output |
| --- | --- | --- |
| Product geometry (approved) | `blender -b --factory-startup --python blender/products/build_products.py` | `blender/products/<id>.blend` |
| Room scenes + previews | `… --python blender/rooms/rooms.py -- living bedroom storage 96` | `blender/rooms/<room>.blend` |
| Final stills (16:9) | `… --python blender/rooms/render_final.py -- 512 2560x1440` | `blender/renders/final/<room>/` |
| Phone cameras (9:16) | `… --python blender/rooms/portrait.py` then `render_final.py -- 512 portrait` | `cam_*_p_*` in the same folder |
| Light probes | `… --python blender/rooms/render_probe.py` | `blender/renders/final/<room>/probe.hdr` |
| GLBs + AO + floor shadows | `npm run glb` | `public/models/` |
| Web images, textures, model maps | `npm run assets` | `public/rooms/`, `public/textures/`, WebP maps in `public/models/`, `src/config/scenes/` |

Source scans are CC0 (Poly Haven, ambientCG) in `blender/assets/` (not versioned).

## Structure

```
src/
  config/rooms.ts         the three rooms: product, cameras (scenes/*.json), exposure
  config/products.ts      copy, finishes, dimensions, components (GLB node names), explode offsets
  config/site.ts          brand strings + WhatsApp number (from env only)
  lib/store.ts            room, view, finishes, quantities, explode, zoom
  lib/whatsapp.ts         pre-filled order link
  three/Stage.tsx         16:9 frame covering the viewport + the WebGL canvas
  three/stage/            Backdrop (stills + parallax), ShotRig (cameras, zoom), LiveProduct (GLB, shadow, hotspot)
  three/furniture/        FurnitureModel: GLB, role-based materials, exploded view + labels
  three/materials.ts      materials matched to blender/products/materials.py
  components/             ShowroomApp + UI (loader, header/room nav, room copy, product panel, no-WebGL fallback)
legacy/                   the earlier procedural showroom, kept for reference (not built)
```

Replacing a model: export a GLB with the same component node names and `role` extras (see `blender/products/export_glb.py`). Finishes and the exploded view need no code changes.

## Performance

- The first room's still is preloaded (16:9 or 9:16 by screen shape); the other rooms and models load once the first room is up.
- Stills are WebP (≈100 KB each), depth maps 8-bit WebP, light probes 512 × 256 HDR, model maps WebP.
- The canvas resolution starts from the device class (2× desktop, 1.5× phones) and steps down by itself if the frame rate drops (drei PerformanceMonitor).
