/**
 * PRODUCT 01 — Lune Coffee Table
 * Two-level construction after the approved reference:
 *  - rounded-rectangle travertine top, offset towards the front-left
 *  - thick dark-walnut lower platform, offset towards the back-right
 *  - asymmetric structure: a dark upright plate at the front-left corner and
 *    a hidden central post towards the back-right
 *  - dark recessed plinth so the platform appears to float
 *
 * Metres, origin at the footprint centre on the floor, front = +Z.
 */
import { assemble, panelGeometry, part, slabGeometry } from "./geometry.ts";

export const COFFEE_TABLE = {
  plinthH: 0.035,
  platformH: 0.09,
  gap: 0.12,
  topH: 0.065,
};

export function buildCoffeeTable() {
  const { plinthH, platformH, gap, topH } = COFFEE_TABLE;
  const platformY = plinthH + platformH / 2;
  const topBottom = plinthH + platformH + gap;
  const topY = topBottom + topH / 2;

  // Top overhangs front-left, platform extends back-right: the layered offset of the reference.
  const top = { w: 1.0, d: 0.82, x: -0.05, z: 0.04 };
  const platform = { w: 1.04, d: 0.74, x: 0.07, z: -0.03 };

  return assemble("coffee-table", [
    part("top", slabGeometry([top.w, topH, top.d], 0.13, 0.006), [top.x, topY, top.z]),
    part("platform", slabGeometry([platform.w, platformH, platform.d], 0.11, 0.012), [platform.x, platformY, platform.z]),
    part("plinth", slabGeometry([0.9, plinthH, 0.6], 0.08, 0.004), [platform.x + 0.02, plinthH / 2, platform.z - 0.02]),
    // Front-left upright: floor to underside of the top, standing just proud of the platform edge.
    part("support", panelGeometry([0.13, topBottom, 0.055], 0.006), [-0.36, topBottom / 2, platform.z + platform.d / 2 - 0.01]),
    // Hidden post carrying the back-right of the top.
    part("post", panelGeometry([0.12, gap, 0.12], 0.004), [0.2, plinthH + platformH + gap / 2, -0.14]),
  ]);
}
