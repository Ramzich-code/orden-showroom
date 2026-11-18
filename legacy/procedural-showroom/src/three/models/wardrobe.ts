/**
 * PRODUCT 03 — Fjell Wardrobe
 * The approved design, unchanged: two flush doors, slim vertical pulls near
 * the centre seam, full-width shelf and rail inside, raised on short legs.
 * Matched to the Warm Minimalism image only in detail: softened vertical
 * edges and longer pulls.
 *
 * Metres, origin at the footprint centre on the floor, front = +Z.
 */
import { assemble, cylinderGeometry, panelGeometry, part } from "./geometry.ts";

export function buildWardrobe() {
  const W = 1.0;
  const H = 1.95;
  const D = 0.58;
  const T = 0.019;
  const Y0 = 0.1;
  const legs = (["fl", "fr", "bl", "br"] as const).map((k) => {
    const x = (k.endsWith("l") ? -1 : 1) * (W / 2 - 0.06);
    const z = (k.startsWith("f") ? 1 : -1) * (D / 2 - 0.06);
    return part(`leg-${k}`, cylinderGeometry(0.02, 0.015, Y0), [x, Y0 / 2, z]);
  });

  return assemble("wardrobe", [
    part("side-l", panelGeometry([T, H, D], 0.008), [-W / 2 + T / 2, Y0 + H / 2, 0]),
    part("side-r", panelGeometry([T, H, D], 0.008), [W / 2 - T / 2, Y0 + H / 2, 0]),
    part("top", panelGeometry([W - 2 * T, T, D]), [0, Y0 + H - T / 2, 0]),
    part("base", panelGeometry([W - 2 * T, T, D]), [0, Y0 + T / 2, 0]),
    part("back", panelGeometry([W - 2 * T, H - 2 * T, 0.008]), [0, Y0 + H / 2, -D / 2 + 0.004]),
    part("shelf", panelGeometry([W - 2 * T, T, D - 0.05]), [0, Y0 + H - 0.34, -0.015]),
    part("rail", cylinderGeometry(0.013, 0.013, W - 2 * T - 0.01, "x"), [0, Y0 + H - 0.42, 0]),
    part("door-l", panelGeometry([W / 2 - 0.004, H - 0.006, 0.022], 0.006), [-W / 4 - 0.001, Y0 + H / 2, D / 2 + 0.013]),
    part("door-r", panelGeometry([W / 2 - 0.004, H - 0.006, 0.022], 0.006), [W / 4 + 0.001, Y0 + H / 2, D / 2 + 0.013]),
    part("handle-l", panelGeometry([0.018, 0.5, 0.022], 0.007), [-0.045, Y0 + 1.0, D / 2 + 0.036]),
    part("handle-r", panelGeometry([0.018, 0.5, 0.022], 0.007), [0.045, Y0 + 1.0, D / 2 + 0.036]),
    ...legs,
  ]);
}
