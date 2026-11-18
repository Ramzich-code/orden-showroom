"use client";

import { useMemo } from "react";
import * as THREE from "three";
import { Environment, Lightformer, Sparkles } from "@react-three/drei";
import { useShowroom } from "@/lib/store";
import { ROOM } from "./roomLayout";

/**
 * Late-morning daylight: a low warm sun through the side window, a procedural
 * environment (no HDR download) for soft bounce and reflections, and dust
 * motes drifting in the beam.
 */
export function Lighting() {
  const quality = useShowroom((s) => s.quality);
  const target = useMemo(() => {
    const o = new THREE.Object3D();
    o.position.set(-1.2, 0, -1.3);
    return o;
  }, []);
  const mapSize = quality === "high" ? 2048 : 1024;

  return (
    <>
      <primitive object={target} />
      <directionalLight
        position={[-11, 7.2, -0.7]}
        target={target}
        color="#FFE6C4"
        intensity={4.2}
        castShadow
        shadow-mapSize={[mapSize, mapSize]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.03}
        shadow-radius={5}
        shadow-camera-left={-6}
        shadow-camera-right={6}
        shadow-camera-top={6}
        shadow-camera-bottom={-6}
        shadow-camera-near={1}
        shadow-camera-far={26}
      />
      <hemisphereLight args={["#F7F2EA", "#C9B497", 0.85]} />

      <Environment resolution={quality === "high" ? 256 : 128} frames={1} environmentIntensity={0.85}>
        {/* window */}
        <Lightformer form="rect" intensity={5} color="#FFF2DD" scale={[3.2, 2.6, 1]} position={[-5, 1.6, -1]} rotation-y={Math.PI / 2} />
        {/* ceiling bounce */}
        <Lightformer form="rect" intensity={1.4} color="#F5F0E8" scale={[9, 7, 1]} position={[0, 3.8, 0]} rotation-x={Math.PI / 2} />
        {/* soft front fill, from the viewer side */}
        <Lightformer form="rect" intensity={1.8} color="#F8F3EB" scale={[8, 3, 1]} position={[0, 1.6, 6]} rotation-y={Math.PI} />
        {/* warm floor bounce */}
        <Lightformer form="rect" intensity={0.3} color="#E6CFAF" scale={[9, 7, 1]} position={[0, -0.5, 0]} rotation-x={-Math.PI / 2} />
      </Environment>

      <Sparkles
        count={quality === "high" ? 70 : 30}
        position={[ROOM.left + 1.9, 1.3, -1.0]}
        scale={[2.6, 2.2, 2.8]}
        size={1.6}
        speed={0.18}
        opacity={0.35}
        color="#FFF3D9"
        noise={0.6}
      />
    </>
  );
}
