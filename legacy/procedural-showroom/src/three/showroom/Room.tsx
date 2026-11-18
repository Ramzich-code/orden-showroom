"use client";

import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { RoundedBox } from "@react-three/drei";
import { PRODUCT_MAP } from "@/config/products";
import { useShowroom } from "@/lib/store";
import { artTexture, floorTexture, noiseTexture, rng, skyTexture } from "../textures";
import { ROOM } from "./roomLayout";

/**
 * The architectural shell and the set dressing (sofa, rug, lamp, plant, art).
 * Set dressing is intentionally simple and replaceable, like the furniture.
 */
export function Room() {
  const mats = useMemo(() => {
    const plasterBump = noiseTexture("plaster", 256, 0.5, [6, 3]);
    const floor = floorTexture();
    floor.repeat.set(ROOM.right - ROOM.left, ROOM.front - ROOM.back);
    return {
      wall: new THREE.MeshStandardMaterial({ color: "#F0EADF", roughness: 0.96, bumpMap: plasterBump, bumpScale: 0.4 }),
      ceiling: new THREE.MeshStandardMaterial({ color: "#EFEAE1", roughness: 1, emissive: "#E9E2D6", emissiveIntensity: 0.55 }),
      trim: new THREE.MeshStandardMaterial({ color: "#EEE9E0", roughness: 0.7 }),
      floor: new THREE.MeshStandardMaterial({ map: floor, roughness: 0.62 }),
      frame: new THREE.MeshStandardMaterial({ color: "#F1EDE6", roughness: 0.55 }),
      sky: new THREE.MeshBasicMaterial({ map: skyTexture(), toneMapped: false }),
    };
  }, []);

  const W = ROOM.right - ROOM.left;
  const Dz = ROOM.front - ROOM.back;
  const cz = (ROOM.front + ROOM.back) / 2;
  const { z0, z1, y0, y1 } = ROOM.window;
  const wx = ROOM.left - 0.1; // left wall centre (0.2 m thick)

  return (
    <group>
      {/* Floor */}
      <mesh rotation-x={-Math.PI / 2} position={[0, 0, cz]} material={mats.floor} receiveShadow>
        <planeGeometry args={[W, Dz]} />
      </mesh>

      {/* Back + right walls */}
      <mesh position={[0, ROOM.height / 2, ROOM.back]} material={mats.wall} receiveShadow>
        <planeGeometry args={[W, ROOM.height]} />
      </mesh>
      <mesh position={[ROOM.right, ROOM.height / 2, cz]} rotation-y={-Math.PI / 2} material={mats.wall} receiveShadow>
        <planeGeometry args={[Dz, ROOM.height]} />
      </mesh>

      {/* Ceiling (casts shadow so sunlight only enters through the window) */}
      <mesh position={[0, ROOM.height + 0.05, cz]} material={mats.ceiling} castShadow receiveShadow>
        <boxGeometry args={[W + 0.6, 0.1, Dz + 0.6]} />
      </mesh>

      {/* Left wall with window opening */}
      <group>
        <WallBlock x={wx} y={[0, y0]} z={[ROOM.back, ROOM.front]} mat={mats.wall} />
        <WallBlock x={wx} y={[y1, ROOM.height]} z={[ROOM.back, ROOM.front]} mat={mats.wall} />
        <WallBlock x={wx} y={[y0, y1]} z={[ROOM.back, z0]} mat={mats.wall} />
        <WallBlock x={wx} y={[y0, y1]} z={[z1, ROOM.front]} mat={mats.wall} />
      </group>

      {/* Window frame: perimeter, one mullion, one transom */}
      <group position={[ROOM.left - 0.06, 0, 0]}>
        {[
          { p: [0, y0 + 0.03, (z0 + z1) / 2], s: [0.08, 0.06, z1 - z0] },
          { p: [0, y1 - 0.03, (z0 + z1) / 2], s: [0.08, 0.06, z1 - z0] },
          { p: [0, (y0 + y1) / 2, z0 + 0.03], s: [0.08, y1 - y0, 0.06] },
          { p: [0, (y0 + y1) / 2, z1 - 0.03], s: [0.08, y1 - y0, 0.06] },
          { p: [0, (y0 + y1) / 2, (z0 + z1) / 2], s: [0.06, y1 - y0, 0.045] },
          { p: [0, 2.2, (z0 + z1) / 2], s: [0.06, 0.045, z1 - z0] },
        ].map((f, i) => (
          <mesh key={i} position={f.p as [number, number, number]} material={mats.frame} castShadow>
            <boxGeometry args={f.s as [number, number, number]} />
          </mesh>
        ))}
        {/* deep sill */}
        <mesh position={[0.12, y0 - 0.01, (z0 + z1) / 2]} material={mats.frame} receiveShadow castShadow>
          <boxGeometry args={[0.28, 0.025, z1 - z0 + 0.1]} />
        </mesh>
      </group>

      {/* Daylight beyond the window */}
      <mesh position={[ROOM.left - 1.6, 1.6, (z0 + z1) / 2]} rotation-y={Math.PI / 2} material={mats.sky}>
        <planeGeometry args={[7, 4.5]} />
      </mesh>

      {/* Skirting */}
      <mesh position={[0, 0.04, ROOM.back + 0.008]} material={mats.trim} receiveShadow>
        <boxGeometry args={[W, 0.08, 0.016]} />
      </mesh>
      <mesh position={[ROOM.right - 0.008, 0.04, cz]} material={mats.trim} receiveShadow>
        <boxGeometry args={[0.016, 0.08, Dz]} />
      </mesh>

      <Curtain />
      <Rug />
      <Sofa />
      <FloorLamp />
      <OliveTree />
      <WallArt />
      <Decor />
    </group>
  );
}

function WallBlock({
  x,
  y,
  z,
  mat,
}: {
  x: number;
  y: [number, number];
  z: [number, number];
  mat: THREE.Material;
}) {
  return (
    <mesh position={[x, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2]} material={mat} castShadow receiveShadow>
      <boxGeometry args={[0.2, y[1] - y[0], z[1] - z[0]]} />
    </mesh>
  );
}

/* ----------------------------------------------------------------- Soft goods */

function Curtain() {
  const ref = useRef<THREE.Mesh>(null);
  const { geo, base } = useMemo(() => {
    const g = new THREE.PlaneGeometry(0.8, 2.72, 60, 1);
    return { geo: g, base: g.attributes.position.array.slice() as Float32Array };
  }, []);
  const mat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: "#F6F1E8",
        roughness: 1,
        transparent: true,
        opacity: 0.62,
        side: THREE.DoubleSide,
      }),
    [],
  );

  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    const pos = geo.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < pos.count; i++) {
      const x = base[i * 3];
      const y = base[i * 3 + 1];
      const lower = (1.36 - y) / 2.72; // 0 at rod, 1 at hem
      pos.setZ(i, Math.sin(x * 34) * 0.028 + Math.sin(x * 9 + t * 0.7) * 0.012 * lower);
    }
    pos.needsUpdate = true;
    geo.computeVertexNormals();
  });

  return (
    <mesh
      ref={ref}
      geometry={geo}
      material={mat}
      position={[ROOM.left + 0.12, 1.42, ROOM.window.z1 + 0.25]}
      rotation-y={Math.PI / 2}
      receiveShadow
    />
  );
}

function Rug() {
  const mat = useMemo(() => {
    const bump = noiseTexture("wool", 256, 1, [10, 8]);
    return new THREE.MeshStandardMaterial({ color: "#EAE3D6", roughness: 1, bumpMap: bump, bumpScale: 1.2 });
  }, []);
  return (
    <RoundedBox args={[3.0, 0.012, 2.15]} radius={0.005} smoothness={2} position={[-0.6, 0.006, -1.45]} material={mat} receiveShadow />
  );
}

function Sofa() {
  const fabric = useMemo(() => {
    const bump = noiseTexture("boucle", 256, 1, [4, 4]);
    return new THREE.MeshPhysicalMaterial({
      color: "#BDB2A1",
      roughness: 0.95,
      sheen: 0.8,
      sheenRoughness: 0.7,
      sheenColor: new THREE.Color("#F2EADC"),
      bumpMap: bump,
      bumpScale: 2,
    });
  }, []);
  const plinth = useMemo(() => new THREE.MeshStandardMaterial({ color: "#2A2825", roughness: 0.6 }), []);
  const cushion = (args: [number, number, number], pos: [number, number, number], rx = 0) => (
    <RoundedBox args={args} radius={0.06} smoothness={4} position={pos} rotation-x={rx} material={fabric} castShadow receiveShadow />
  );
  return (
    <group position={[-0.6, 0, -2.97]}>
      <mesh position={[0, 0.02, 0]} material={plinth} receiveShadow>
        <boxGeometry args={[2.28, 0.04, 0.84]} />
      </mesh>
      {cushion([2.4, 0.22, 0.95], [0, 0.15, 0])}
      {cushion([1.0, 0.17, 0.76], [-0.51, 0.34, 0.08])}
      {cushion([1.0, 0.17, 0.76], [0.51, 0.34, 0.08])}
      {cushion([1.0, 0.44, 0.22], [-0.51, 0.62, -0.33], -0.12)}
      {cushion([1.0, 0.44, 0.22], [0.51, 0.62, -0.33], -0.12)}
      {cushion([0.18, 0.5, 0.95], [-1.11, 0.36, 0])}
      {cushion([0.18, 0.5, 0.95], [1.11, 0.36, 0])}
    </group>
  );
}

/* --------------------------------------------------------------- Accessories */

function FloorLamp() {
  const metal = useMemo(() => new THREE.MeshStandardMaterial({ color: "#2B2926", metalness: 0.6, roughness: 0.4 }), []);
  const shade = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: "#F1E9DA",
        emissive: "#FFD9A6",
        emissiveIntensity: 0.12,
        roughness: 1,
        side: THREE.DoubleSide,
      }),
    [],
  );
  return (
    <group position={[-2.3, 0, -3.05]}>
      <mesh position={[0, 0.012, 0]} material={metal} castShadow receiveShadow>
        <cylinderGeometry args={[0.16, 0.17, 0.024, 40]} />
      </mesh>
      <mesh position={[0, 0.76, 0]} material={metal} castShadow>
        <cylinderGeometry args={[0.009, 0.009, 1.5, 12]} />
      </mesh>
      <mesh position={[0, 1.58, 0]} material={shade} castShadow>
        <cylinderGeometry args={[0.17, 0.22, 0.32, 48, 1, true]} />
      </mesh>
      <pointLight position={[0, 1.5, 0]} intensity={1.6} distance={3.5} decay={2} color="#FFD7A3" />
    </group>
  );
}

function OliveTree() {
  const leaves = useRef<THREE.InstancedMesh>(null);
  const canopy = useRef<THREE.Group>(null);
  const COUNT = 420;
  const mats = useMemo(
    () => ({
      pot: new THREE.MeshStandardMaterial({ color: "#3A3733", roughness: 0.85 }),
      soil: new THREE.MeshStandardMaterial({ color: "#3B2F25", roughness: 1 }),
      bark: new THREE.MeshStandardMaterial({ color: "#6E6152", roughness: 0.9 }),
      leaf: new THREE.MeshStandardMaterial({ color: "#6F7858", roughness: 0.75, side: THREE.DoubleSide }),
    }),
    [],
  );
  const leafGeo = useMemo(() => {
    const g = new THREE.SphereGeometry(1, 6, 4);
    g.scale(0.055, 0.008, 0.017);
    return g;
  }, []);

  useLayoutEffect(() => {
    const r = rng(42);
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const e = new THREE.Euler();
    const clusters: [number, number, number, number][] = [
      [0, 1.85, 0, 0.42],
      [-0.25, 1.55, 0.12, 0.3],
      [0.22, 1.6, -0.1, 0.32],
      [0.05, 2.15, 0.05, 0.28],
    ];
    for (let i = 0; i < COUNT; i++) {
      const [cx, cy, cz, cr] = clusters[i % clusters.length];
      const u = r() * Math.PI * 2;
      const v = Math.acos(2 * r() - 1);
      const rad = cr * Math.cbrt(r());
      const p = new THREE.Vector3(
        cx + rad * Math.sin(v) * Math.cos(u),
        cy + rad * Math.cos(v) * 0.75,
        cz + rad * Math.sin(v) * Math.sin(u),
      );
      e.set((r() - 0.5) * 1.6, r() * Math.PI * 2, (r() - 0.5) * 1.6);
      q.setFromEuler(e);
      const s = 0.7 + r() * 0.6;
      m.compose(p, q, new THREE.Vector3(s, s, s));
      leaves.current!.setMatrixAt(i, m);
    }
    leaves.current!.instanceMatrix.needsUpdate = true;
  }, []);

  useFrame(({ clock }) => {
    if (!canopy.current) return;
    const t = clock.elapsedTime;
    canopy.current.rotation.z = Math.sin(t * 0.6) * 0.012;
    canopy.current.rotation.x = Math.sin(t * 0.45 + 1) * 0.008;
  });

  return (
    <group position={[-3.85, 0, -2.95]}>
      <mesh position={[0, 0.24, 0]} material={mats.pot} castShadow receiveShadow>
        <cylinderGeometry args={[0.25, 0.2, 0.48, 40]} />
      </mesh>
      <mesh position={[0, 0.465, 0]} material={mats.soil}>
        <cylinderGeometry args={[0.23, 0.23, 0.01, 32]} />
      </mesh>
      <group ref={canopy}>
        <mesh position={[0, 1.0, 0]} rotation-z={0.06} material={mats.bark} castShadow>
          <cylinderGeometry args={[0.018, 0.03, 1.1, 8]} />
        </mesh>
        <mesh position={[-0.12, 1.45, 0.06]} rotation={[0.3, 0, 0.6]} material={mats.bark} castShadow>
          <cylinderGeometry args={[0.008, 0.014, 0.5, 6]} />
        </mesh>
        <mesh position={[0.1, 1.5, -0.05]} rotation={[-0.25, 0, -0.5]} material={mats.bark} castShadow>
          <cylinderGeometry args={[0.008, 0.014, 0.5, 6]} />
        </mesh>
        <instancedMesh ref={leaves} args={[leafGeo, mats.leaf, COUNT]} castShadow />
      </group>
    </group>
  );
}

function WallArt() {
  const oak = useMemo(() => new THREE.MeshStandardMaterial({ color: "#B88B5E", roughness: 0.6 }), []);
  const prints = useMemo(
    () => [0, 1].map((v) => new THREE.MeshStandardMaterial({ map: artTexture(v as 0 | 1), roughness: 0.9 })),
    [],
  );
  const frames: { x: number; y: number; w: number; h: number; art: number }[] = [
    { x: -1.05, y: 1.72, w: 0.56, h: 0.74, art: 0 },
    { x: -0.2, y: 1.62, w: 0.46, h: 0.6, art: 1 },
  ];
  return (
    <group position={[0, 0, ROOM.back]}>
      {frames.map((f, i) => (
        <group key={i} position={[f.x, f.y, 0.02]}>
          <mesh material={oak} castShadow receiveShadow>
            <boxGeometry args={[f.w, f.h, 0.03]} />
          </mesh>
          <mesh position={[0, 0, 0.0155]} material={prints[f.art]}>
            <planeGeometry args={[f.w - 0.04, f.h - 0.04]} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

/**
 * Objects styled on top of products. Hidden while their product is in focus,
 * so the product viewer and exploded view show the piece alone.
 */
function Decor() {
  const selected = useShowroom((s) => s.selectedId);
  const mats = useMemo(
    () => ({
      ceramic: new THREE.MeshStandardMaterial({ color: "#E9E4DA", roughness: 0.5, side: THREE.DoubleSide }),
      stone: new THREE.MeshStandardMaterial({ color: "#8E8678", roughness: 0.8 }),
      bookA: new THREE.MeshStandardMaterial({ color: "#C7B79C", roughness: 0.85 }),
      bookB: new THREE.MeshStandardMaterial({ color: "#3A3834", roughness: 0.85 }),
    }),
    [],
  );
  const vase = useMemo(() => {
    const pts = [
      [0, 0],
      [0.06, 0],
      [0.075, 0.06],
      [0.06, 0.16],
      [0.03, 0.22],
      [0.035, 0.26],
    ].map(([x, y]) => new THREE.Vector2(x, y));
    return new THREE.LatheGeometry(pts, 40);
  }, []);
  const bowl = useMemo(() => new THREE.SphereGeometry(0.13, 40, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), []);

  const coffee = PRODUCT_MAP["coffee-table"].showroom;
  const bedside = PRODUCT_MAP["bedside-table"].showroom;
  const ct = coffee.position;
  const bt = bedside.position;

  return (
    <>
      {selected !== "coffee-table" && (
        <group position={[ct[0] - 0.05, coffee.surfaceY, ct[2] + 0.04]}>
          <mesh position={[0.28, 0.018, 0.04]} rotation-y={0.12} material={mats.bookA} castShadow receiveShadow>
            <boxGeometry args={[0.3, 0.036, 0.22]} />
          </mesh>
          <mesh position={[0.29, 0.051, 0.03]} rotation-y={-0.08} material={mats.bookB} castShadow receiveShadow>
            <boxGeometry args={[0.24, 0.03, 0.18]} />
          </mesh>
          <mesh geometry={bowl} position={[-0.24, 0.13, -0.04]} material={mats.ceramic} castShadow receiveShadow />
          <mesh position={[-0.24, 0.035, -0.04]} material={mats.stone} castShadow>
            <sphereGeometry args={[0.035, 20, 12]} />
          </mesh>
        </group>
      )}
      {selected !== "bedside-table" && (
        <group position={[bt[0] + 0.13, bedside.surfaceY, bt[2] - 0.02]}>
          <mesh geometry={vase} material={mats.ceramic} castShadow receiveShadow />
        </group>
      )}
    </>
  );
}
