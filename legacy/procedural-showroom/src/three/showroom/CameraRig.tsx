"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import gsap from "gsap";
import { useFrame, useThree } from "@react-three/fiber";
import { useShowroom } from "@/lib/store";
import { PRODUCT_MAP } from "@/config/products";

const DESKTOP = { pos: new THREE.Vector3(1.35, 1.42, 4.3), target: new THREE.Vector3(-0.2, 0.95, -1.7), fov: 40 };
const PORTRAIT = { pos: new THREE.Vector3(-0.35, 1.3, 5.0), target: new THREE.Vector3(-0.35, 1.18, -1.7), fov: 50 };
const PAN_RANGE: [number, number] = [-2.0, 2.6];
const INTRO_OFFSET = new THREE.Vector3(0.6, 0.45, 2.4);

/**
 * Showroom camera: a slow cinematic dolly-in after the loader, gentle
 * breathing, mouse parallax on desktop and drag-to-pan (mouse or touch).
 */
export function CameraRig() {
  const { camera, gl, size } = useThree();
  const entered = useShowroom((s) => s.entered);
  const intro = useRef({ t: 1 });
  const pan = useRef({ current: 0, target: 0 });
  const pointerKind = useRef<"mouse" | "touch">("mouse");
  const look = useRef(new THREE.Vector3().copy(DESKTOP.target));
  const desired = useRef(new THREE.Vector3());
  const desiredTarget = useRef(new THREE.Vector3());

  // Intro dolly
  useEffect(() => {
    if (!entered) return;
    const tween = gsap.to(intro.current, { t: 0, duration: 3.4, ease: "power3.inOut" });
    return () => {
      tween.kill();
    };
  }, [entered]);

  // Drag to pan
  useEffect(() => {
    const el = gl.domElement;
    let dragging = false;
    let lastX = 0;
    const down = (e: PointerEvent) => {
      pointerKind.current = e.pointerType === "mouse" ? "mouse" : "touch";
      dragging = true;
      lastX = e.clientX;
    };
    const move = (e: PointerEvent) => {
      if (e.pointerType === "mouse") pointerKind.current = "mouse";
      if (!dragging || useShowroom.getState().view !== "showroom") return;
      const dx = e.clientX - lastX;
      lastX = e.clientX;
      const k = 5 / Math.max(el.clientWidth, 1);
      pan.current.target = THREE.MathUtils.clamp(pan.current.target - dx * k, PAN_RANGE[0], PAN_RANGE[1]);
    };
    const up = () => {
      dragging = false;
    };
    el.addEventListener("pointerdown", down);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    window.addEventListener("pointercancel", up);
    return () => {
      el.removeEventListener("pointerdown", down);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("pointercancel", up);
    };
  }, [gl]);

  useFrame((state, dt) => {
    const cam = camera as THREE.PerspectiveCamera;
    const portrait = size.width / size.height < 1;
    const frame = portrait ? PORTRAIT : DESKTOP;

    if (Math.abs(cam.fov - frame.fov) > 0.01) {
      cam.fov = frame.fov;
      cam.updateProjectionMatrix();
    }

    const t = state.clock.elapsedTime;
    const p = pan.current;
    p.current += (p.target - p.current) * (1 - Math.exp(-dt * 4));

    const parallax = pointerKind.current === "mouse" ? state.pointer : { x: 0, y: 0 };
    const i = intro.current.t;

    desired.current
      .copy(frame.pos)
      .addScaledVector(INTRO_OFFSET, i)
      .add({ x: p.current + parallax.x * 0.22, y: parallax.y * 0.08 + Math.sin(t * 0.35) * 0.025, z: 0 });
    desiredTarget.current.copy(frame.target).add({ x: p.current + parallax.x * 0.08, y: i * 0.15, z: 0 });

    // Product focus: fly to the framing configured for the selected piece.
    const selected = useShowroom.getState().selectedId;
    if (selected) {
      const shot = PRODUCT_MAP[selected].showroom.camera;
      desired.current.set(...shot.position);
      desiredTarget.current.set(...shot.target);
    }

    const k = 1 - Math.exp(-dt * 3);
    cam.position.lerp(desired.current, k);
    look.current.lerp(desiredTarget.current, k);
    cam.lookAt(look.current);
  });

  return null;
}
