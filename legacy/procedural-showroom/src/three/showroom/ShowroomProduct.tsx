"use client";

import { useRef } from "react";
import * as THREE from "three";
import { ThreeEvent, useFrame } from "@react-three/fiber";
import { Html, useCursor } from "@react-three/drei";
import type { Product } from "@/config/products";
import { useShowroom } from "@/lib/store";
import { FurnitureModel } from "../furniture/FurnitureModel";

/** A product placed in the room, with hover feedback and a hotspot pin. */
export function ShowroomProduct({ product }: { product: Product }) {
  const finish = useShowroom((s) => s.finishes[product.id]);
  const hovered = useShowroom((s) => s.hoveredId === product.id && s.view === "showroom");
  const showPins = useShowroom((s) => s.entered && s.view === "showroom");
  const setHovered = useShowroom((s) => s.setHovered);
  const ring = useRef<THREE.Mesh>(null);
  const { position, rotationY, hotspot, footprint } = product.showroom;

  useCursor(hovered);

  useFrame((_, dt) => {
    if (!ring.current) return;
    const m = ring.current.material as THREE.MeshBasicMaterial;
    const k = 1 - Math.exp(-dt * 8);
    m.opacity += ((hovered ? 0.55 : 0) - m.opacity) * k;
    const s = ring.current.scale.x + ((hovered ? 1 : 0.9) - ring.current.scale.x) * k;
    ring.current.scale.setScalar(s);
  });

  const over = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    if (e.pointerType === "mouse") setHovered(product.id);
  };
  const out = () => {
    if (useShowroom.getState().hoveredId === product.id) setHovered(null);
  };

  return (
    <group position={position} rotation-y={rotationY}>
      <group onPointerOver={over} onPointerOut={out}>
        <FurnitureModel product={product} finish={finish} />
      </group>

      <mesh ref={ring} rotation-x={-Math.PI / 2} position-y={0.016} scale={0.9}>
        <ringGeometry args={[footprint, footprint + 0.01, 128]} />
        <meshBasicMaterial color="#FFFBF3" transparent opacity={0} depthWrite={false} toneMapped={false} />
      </mesh>

      {showPins && (
        <Html position={hotspot} center zIndexRange={[30, 10]}>
          <div
            className="hotspot"
            data-active={hovered || undefined}
            data-side={product.showroom.labelSide ?? "right"}
            onPointerEnter={() => setHovered(product.id)}
            onPointerLeave={out}
          >
            <span className="hotspot-dot" aria-hidden />
            <span className="hotspot-label">
              <span className="hotspot-index">{product.index}</span>
              {product.name}
            </span>
          </div>
        </Html>
      )}
    </group>
  );
}
