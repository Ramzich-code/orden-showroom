# ORDEN — Asset shortlist for approval

**Status:** proposal only. Nothing has been downloaded.
**Sources:** Poly Haven and ambientCG, both **CC0 (public domain)**: free for commercial use, no attribution required.
**Sizes** are the published download sizes of the PBR map set (Color, Roughness, Normal GL, Displacement) at the resolution listed.
Originals stay in `blender/assets/` and are excluded from the website. The site only ships compressed derivatives.

A visual sheet of every candidate I compared (145 items) is in `docs/assets-review/candidates.html`.

---

## Batch A — needed now for Phase 1–2 (product materials and product renders) · ≈ 154 MB

| # | Asset | Used for | Preview | Source | Licence | Res. | Size |
|---|---|---|---|---|---|---|---|
| A1 | **Travertine009** | Coffee table top (cream, fine bedding lines) | ![](https://acg-media.struffelproductions.com/file/ambientCG-Web/media/thumbnail/256-PNG/Travertine009.png) | [ambientCG](https://ambientcg.com/view?id=Travertine009) | CC0 | 4K | 31.3 MB |
| A2 | **Marble019** | Bedside table top (white, soft grey veins) | ![](https://acg-media.struffelproductions.com/file/ambientCG-Web/media/thumbnail/256-PNG/Marble019.png) | [ambientCG](https://ambientcg.com/view?id=Marble019) | CC0 | 4K | 32.8 MB |
| A3 | **Walnut Veneer** | Coffee table platform (Signature) | ![](https://cdn.polyhaven.com/asset_img/thumbs/walnut_veneer.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/walnut_veneer) | CC0 | 4K | 27.8 MB |
| A4 | **Oak Veneer 02** | "Natural Oak" finish, all three products | ![](https://cdn.polyhaven.com/asset_img/thumbs/oak_veneer_02.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/oak_veneer_02) | CC0 | 4K | 28.6 MB |
| A5 | **Fingerprints003** | Subtle roughness wear on lacquer and stone (imperfections) | ![](https://acg-media.struffelproductions.com/file/ambientCG-Web/media/thumbnail/256-PNG/Fingerprints003.png) | [ambientCG](https://ambientcg.com/view?id=Fingerprints003) | CC0 | 2K | 10.1 MB |
| A6 | **Studio Small 09** (HDRI) | Studio lighting for product renders and web product viewer | ![](https://cdn.polyhaven.com/asset_img/thumbs/studio_small_09.png?width=256&height=128) | [Poly Haven](https://polyhaven.com/a/studio_small_09) | CC0 | 4K | 23.5 MB |

Painted finishes (White, Black, Taupe, Greige) need **no texture download**. They are built as physically based matte lacquer: colour, roughness ≈ 0.45–0.6, a thin clear coat, and A5 driving micro-variation in roughness.

**Alternates, in case a primary doesn't render well:** Travertine001 (32.5 MB), Marble021 (32.9 MB), Black Walnut Veneer 02 (27.8 MB), White Oak Veneer (30.9 MB).

---

## Batch B — needed later for Phase 3 (showroom rebuild) · ≈ 158 MB

| # | Asset | Used for | Preview | Source | Licence | Res. | Size |
|---|---|---|---|---|---|---|---|
| B1 | **Laminate Floor 02** | Light oak plank floor | ![](https://cdn.polyhaven.com/asset_img/thumbs/laminate_floor_02.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/laminate_floor_02) | CC0 | 4K | 40.7 MB |
| B2 | **Beige Wall 001** | Walls (warm off-white plaster) | ![](https://cdn.polyhaven.com/asset_img/thumbs/beige_wall_001.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/beige_wall_001) | CC0 | 4K | 8.5 MB |
| B3 | **Curly Teddy Natural** | Sofa upholstery (cream bouclé look) | ![](https://cdn.polyhaven.com/asset_img/thumbs/curly_teddy_natural.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/curly_teddy_natural) | CC0 | 4K | 28.3 MB |
| B4 | **Rough Linen** | Sheer curtain | ![](https://cdn.polyhaven.com/asset_img/thumbs/rough_linen.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/rough_linen) | CC0 | 2K | 14.3 MB |
| B5 | **Carpet016** | Rug (cream wool) | ![](https://acg-media.struffelproductions.com/file/ambientCG-Web/media/thumbnail/256-PNG/Carpet016.png) | [ambientCG](https://ambientcg.com/view?id=Carpet016) | CC0 | 2K | 29.8 MB |
| B6 | **Symmetrical Garden 02** (HDRI) | Daylight and garden seen through the window | ![](https://cdn.polyhaven.com/asset_img/thumbs/symmetrical_garden_02.png?width=256&height=128) | [Poly Haven](https://polyhaven.com/a/symmetrical_garden_02) | CC0 | 4K | 25.6 MB |
| B7 | **Potted Plant 01** (model) | Corner plant; its terracotta pot gets re-materialed in matte stoneware | ![](https://cdn.polyhaven.com/asset_img/thumbs/potted_plant_01.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/potted_plant_01) | CC0 | 2K glTF | 8.6 MB |
| B8 | **Ceramic Vase 02** (model) | Styling on the bedside table / sideboard | ![](https://cdn.polyhaven.com/asset_img/thumbs/ceramic_vase_02.png?width=256&height=256) | [Poly Haven](https://polyhaven.com/a/ceramic_vase_02) | CC0 | 2K glTF | 2.0 MB |

Sunlight comes from Blender's built-in physical **Nishita sky** (exact sun angle and colour, nothing to download).

---

## Gaps: what the free libraries cannot supply well

- **Sofa:** Poly Haven's sofas (Sofa 01/02/03, Chinese Sofa) are classical or antique styles that would clash with ORDEN. ambientCG has no models. **Proposal:** model a minimal low sofa in Blender with B3. Alternatively, a licensed paid model (CGTrader, Evermotion, roughly €20–80), which would need your purchase approval.
- **Floor lamp, books, small bowl:** nothing suitable or modern in CC0. I'll model these in Blender. They are simple hard-surface objects.
- **Wall art:** keep ORDEN's own original artwork, printed on a canvas or paper material.

**Total if everything is approved: ≈ 312 MB** (Batch A ≈ 154 MB now, Batch B ≈ 158 MB at Phase 3).
