"use client";

import { use, useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import type { FinishId, ProductId } from "@/config/products";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Html, useCursor, useGLTF, useTexture } from "@react-three/drei";
import { PRODUCT_MAP } from "@/config/products";
import { RoomId, placement } from "@/config/rooms";
import { useShowroom } from "@/lib/store";
import { FurnitureModel } from "../furniture/FurnitureModel";
import { runtime } from "./runtime";
import { JOURNEY } from "@/config/journey";
import { useJourney } from "@/lib/journey";

/**
 * A real-time product, standing exactly where its Cycles twin stands. Hidden
 * while the beauty still is shown; an invisible box still takes the hover /
 * click, and the hotspot pin sits above it. Only the selected piece turns and
 * explodes; the others stay put in its product view.
 */
export function LiveProduct({ room, productId }: { room: RoomId; productId: ProductId }) {
  const place = placement(room, productId);
  const product = PRODUCT_MAP[productId];
  const finish = useShowroom((s) => s.finishes[productId]);
  const view = useShowroom((s) => s.view);
  const selected = useShowroom((s) => s.selected === productId);
  const hovered = useShowroom((s) => s.hovered === productId);
  const entered = useShowroom((s) => s.entered);
  const switching = useShowroom((s) => s.switching);
  const exploded = useShowroom((s) => s.exploded && s.selected === productId);
  const setHovered = useShowroom((s) => s.setHovered);
  const openProduct = useShowroom((s) => s.openProduct);

  const { scene: gltf } = useGLTF(product.model);
  const box = useMemo(() => new THREE.Box3().setFromObject(gltf), [gltf]);
  const boxSize = useMemo(() => box.getSize(new THREE.Vector3()), [box]);
  const boxCenter = useMemo(() => box.getCenter(new THREE.Vector3()), [box]);

  const live = useRef<THREE.Group>(null);
  const turn = useRef<THREE.Group>(null);
  const explodeRef = useRef(0);

  // finish crossfade: the previous finish stays on top and dissolves away
  const [prevFinish, setPrevFinish] = useState<FinishId | null>(null);
  const fadeRef = useRef(0);
  const lastFinish = useRef(finish);
  useEffect(() => {
    if (lastFinish.current === finish) return;
    const from = lastFinish.current;
    lastFinish.current = finish;
    if (runtime.live < 0.5) return; // not on screen: nothing to dissolve
    setPrevFinish(from);
    fadeRef.current = 1;
    const tw = gsap.to(fadeRef, { current: 0, duration: 0.75, ease: "power1.inOut", onComplete: () => setPrevFinish(null) });
    return () => {
      tw.kill();
    };
  }, [finish]);

  useCursor(hovered && view === "room");

  useFrame(() => {
    const active = useShowroom.getState().selected === productId;
    explodeRef.current = active ? runtime.explode : 0;
    if (live.current) live.current.visible = runtime.live > 0.001;
    if (turn.current) turn.current.rotation.y = active ? runtime.rotation : 0;
  });

  const resting = useJourney((s) => JOURNEY[s.step].kind === "rest" && s.cover < 0.05);
  const inRoom = view === "room" && entered && !switching && resting;

  return (
    <group position={place.position} rotation-y={place.rotation_y} name={productId}>
      <group ref={live}>
        <group ref={turn}>
          <FurnitureModel product={product} finish={finish} explodeRef={explodeRef} labels={exploded} />
          {prevFinish && <FurnitureModel key={prevFinish} product={product} finish={prevFinish} explodeRef={explodeRef} fadeRef={fadeRef} />}
          <ShadowCard model={product.model} active={selected} />
        </group>
      </group>

      <mesh
        position={boxCenter}
        onPointerOver={(e) => {
          e.stopPropagation();
          if (useShowroom.getState().view === "room") setHovered(productId);
        }}
        onPointerOut={() => useShowroom.getState().hovered === productId && setHovered(null)}
        onClick={(e) => {
          e.stopPropagation();
          if (useShowroom.getState().view === "room") openProduct(productId);
        }}
      >
        <boxGeometry args={[boxSize.x, boxSize.y, boxSize.z]} />
        <meshBasicMaterial visible={false} />
      </mesh>

      {inRoom && (
        <Html position={[0, product.hotspotY, 0]} center zIndexRange={[30, 10]}>
          <button
            type="button"
            className="hotspot"
            data-active={hovered || undefined}
            onPointerEnter={() => setHovered(productId)}
            onPointerLeave={() => useShowroom.getState().hovered === productId && setHovered(null)}
            onClick={() => openProduct(productId)}
            aria-label={`Discover the ${product.name}`}
          >
            <span className="hotspot-dot" aria-hidden />
            <span className="hotspot-label">
              <span className="hotspot-index">{product.index}</span>
              {product.name}
            </span>
          </button>
        </Html>
      )}
    </group>
  );
}

type CardInfo = { center: [number, number]; size: [number, number] };
const cards = new Map<string, Promise<CardInfo>>();
const cardInfo = (url: string) => {
  if (!cards.has(url)) cards.set(url, fetch(url).then((r) => r.json()));
  return cards.get(url)!;
};

/**
 * The floor occlusion the product casts, baked in Cycles with the product
 * (public/models/<id>_shadow.png + .json, from export_glb.py). A static card
 * under the live product: same softness as the stills, no real-time pass.
 */
function ShadowCard({ model, active }: { model: string; active: boolean }) {
  const base = model.replace(/.glb$/, "_shadow");
  const map = useTexture(`${base}.webp`);
  const info = use(cardInfo(`${base}.json`));
  const material = useRef<THREE.MeshBasicMaterial>(null);
  // the card is the assembled product's shadow: let it fade as the parts move apart
  useFrame(() => {
    if (material.current) material.current.opacity = 0.82 * (1 - 0.65 * (active ? runtime.explode : 0));
  });
  return (
    <mesh rotation-x={-Math.PI / 2} position={[info.center[0], 0.002, info.center[1]]} renderOrder={-1}>
      <planeGeometry args={info.size} />
      <meshBasicMaterial ref={material} map={map} transparent opacity={0.82} depthWrite={false} color="#1b140f" toneMapped={false} />
    </mesh>
  );
}
