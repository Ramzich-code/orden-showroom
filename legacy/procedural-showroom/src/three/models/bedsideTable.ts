/**
 * PRODUCT 02 — Hvile Bedside Table
 * After the approved reference:
 *  - taupe painted carcass; the two sides and the back stand ~2 cm proud of
 *    the top, framing it like a tray
 *  - white marble-effect top set inside that frame
 *  - open central shelf, large handleless drawer below (shadow-gap pull)
 *  - dark recessed plinth
 *
 * Metres, origin at the footprint centre on the floor, front = +Z.
 */
import { assemble, panelGeometry, part, slabGeometry } from "./geometry.ts";

export const BEDSIDE_TABLE = { width: 0.6, depth: 0.4, height: 0.44 };

export function buildBedsideTable() {
  const W = BEDSIDE_TABLE.width;
  const D = BEDSIDE_TABLE.depth;
  const H = BEDSIDE_TABLE.height;
  const t = 0.02; // panel thickness
  const plinthH = 0.04;
  const bodyH = H - plinthH;
  const innerW = W - 2 * t;
  const innerD = D - t;
  const marbleH = 0.035;
  const marbleTop = H - 0.02; // sits 2 cm below the raised frame
  const drawerBottom = plinthH + t + 0.004;
  const drawerTop = plinthH + 0.215;
  const drawerH = drawerTop - drawerBottom;
  const shelfY = drawerTop + 0.004 + 0.009;
  const zInner = t / 2; // centre of the space in front of the back panel

  return assemble("bedside-table", [
    part("side-l", panelGeometry([t, bodyH, D], 0.003), [-W / 2 + t / 2, plinthH + bodyH / 2, 0]),
    part("side-r", panelGeometry([t, bodyH, D], 0.003), [W / 2 - t / 2, plinthH + bodyH / 2, 0]),
    part("back", panelGeometry([innerW, bodyH, t], 0.002), [0, plinthH + bodyH / 2, -D / 2 + t / 2]),
    part("bottom", panelGeometry([innerW, t, innerD]), [0, plinthH + t / 2, zInner]),
    part("shelf", panelGeometry([innerW, 0.018, innerD - 0.004], 0.002), [0, shelfY, zInner - 0.002]),
    part("top", slabGeometry([innerW - 0.002, marbleH, innerD - 0.002], 0.004, 0.003), [0, marbleTop - marbleH / 2, zInner]),
    part("drawer-front", panelGeometry([innerW - 0.006, drawerH, 0.02], 0.002), [0, drawerBottom + drawerH / 2, D / 2 - 0.01]),
    part("drawer-box", panelGeometry([innerW - 0.03, drawerH - 0.04, innerD - 0.05]), [0, drawerBottom + (drawerH - 0.04) / 2 + 0.01, -0.01]),
    part("plinth", panelGeometry([W - 0.06, plinthH, D - 0.06]), [0, plinthH / 2, -0.01]),
  ]);
}
