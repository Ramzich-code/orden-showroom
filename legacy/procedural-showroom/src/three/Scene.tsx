"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { AdaptiveDpr, PerformanceMonitor, Preload } from "@react-three/drei";
import { PRODUCTS } from "@/config/products";
import { useShowroom } from "@/lib/store";
import { Room } from "./showroom/Room";
import { Lighting } from "./showroom/Lighting";
import { ShowroomProduct } from "./showroom/ShowroomProduct";
import { CameraRig } from "./showroom/CameraRig";

/** Flags the scene as ready once a few frames have actually rendered. */
function ReadySignal() {
  const setSceneReady = useShowroom((s) => s.setSceneReady);
  const frames = useRef(0);
  useFrame(() => {
    frames.current++;
    if (frames.current === 3) setSceneReady();
  });
  return null;
}

/**
 * The single WebGL canvas. Loaded lazily (client only) from ShowroomApp.
 */
export default function Scene() {
  const quality = useShowroom((s) => s.quality);
  const [dpr, setDpr] = useState(quality === "high" ? 1.75 : 1.25);

  useEffect(() => setDpr(quality === "high" ? 1.75 : 1.25), [quality]);

  return (
    <Canvas
      shadows="percentage"
      dpr={[1, dpr]}
      camera={{ fov: 38, near: 0.05, far: 60, position: [0.95, 1.95, 7] }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      style={{ touchAction: "none" }}
      onCreated={({ gl }) => {
        gl.toneMapping = THREE.NeutralToneMapping;
        gl.toneMappingExposure = 1.0;
      }}
    >
      <color attach="background" args={["#E7E0D4"]} />
      <fog attach="fog" args={["#E7E0D4", 10, 24]} />

      <PerformanceMonitor onDecline={() => setDpr(1)} onIncline={() => setDpr(quality === "high" ? 1.75 : 1.25)} />
      <AdaptiveDpr pixelated={false} />

      <Suspense fallback={null}>
        <Lighting />
        <Room />
        {PRODUCTS.map((p) => (
          <ShowroomProduct key={p.id} product={p} />
        ))}
        <ReadySignal />
        <Preload all />
      </Suspense>

      <CameraRig />
    </Canvas>
  );
}
