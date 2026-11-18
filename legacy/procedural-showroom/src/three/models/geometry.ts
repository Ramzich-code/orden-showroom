/**
 * Geometry helpers shared by the model factories. Pure three.js (no DOM), so
 * the same code runs in the browser and in the GLB export script
 * (`npm run models`).
 */
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

export type V3 = [number, number, number];

/** Neutral placeholder; the site assigns real materials by component role. */
const PLACEHOLDER = new THREE.MeshStandardMaterial({ color: "#bbbbbb", roughness: 0.6 });

function roundedRectShape(w: number, d: number, r: number) {
  const s = new THREE.Shape();
  const x = -w / 2;
  const y = -d / 2;
  r = Math.min(r, w / 2, d / 2);
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y);
  s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + d - r);
  s.quadraticCurveTo(x + w, y + d, x + w - r, y + d);
  s.lineTo(x + r, y + d);
  s.quadraticCurveTo(x, y + d, x, y + d - r);
  s.lineTo(x, y + r);
  s.quadraticCurveTo(x, y, x + r, y);
  return s;
}

/**
 * Horizontal slab with rounded plan corners and softened (bevelled) edges.
 * `size` is the finished outer size [width (x), height (y), depth (z)],
 * centred on the origin.
 */
export function slabGeometry(size: V3, cornerRadius: number, edge = 0.006) {
  const [w, h, d] = size;
  const e = Math.min(edge, h / 2 - 0.0005);
  const shape = roundedRectShape(w - 2 * e, d - 2 * e, Math.max(cornerRadius - e, 0.001));
  const g = new THREE.ExtrudeGeometry(shape, {
    depth: h - 2 * e,
    bevelEnabled: e > 0,
    bevelThickness: e,
    bevelSize: e,
    bevelSegments: 4,
    curveSegments: 18,
  });
  // Extrusion runs along +Z; stand it up so thickness is along Y.
  g.rotateX(-Math.PI / 2);
  g.translate(0, -(h - 2 * e) / 2, 0);
  g.computeVertexNormals();
  return g;
}

/** Box with eased edges (or a plain box when radius is 0). */
export function panelGeometry(size: V3, radius = 0) {
  if (radius <= 0) return new THREE.BoxGeometry(...size);
  return new RoundedBoxGeometry(size[0], size[1], size[2], 3, radius);
}

export function cylinderGeometry(radiusTop: number, radiusBottom: number, height: number, axis: "x" | "y" | "z" = "y") {
  const g = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, 32);
  if (axis === "x") g.rotateZ(Math.PI / 2);
  if (axis === "z") g.rotateX(Math.PI / 2);
  return g;
}

/**
 * One separable component: a named group (the node the exploded view moves)
 * holding a single mesh.
 */
export function part(id: string, geometry: THREE.BufferGeometry, position: V3, rotation?: V3) {
  const group = new THREE.Group();
  group.name = id;
  group.position.set(...position);
  if (rotation) group.rotation.set(...rotation);
  const mesh = new THREE.Mesh(geometry, PLACEHOLDER);
  mesh.name = `${id}_mesh`;
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return group;
}

export function assemble(name: string, parts: THREE.Object3D[]) {
  const root = new THREE.Group();
  root.name = name;
  parts.forEach((p) => root.add(p));
  return root;
}
