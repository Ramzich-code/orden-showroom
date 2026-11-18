"use client";

import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import gsap from "gsap";
import { useFrame, useThree } from "@react-three/fiber";
import { Orientation, ROOM_MAP, RoomId, sceneCameras } from "@/config/rooms";
import { useShowroom } from "@/lib/store";
import { cropAround, matchCrops, productFocus } from "./focus";
import { IMAGE_LAYER, runtime } from "./runtime";

const PARALLAX = new THREE.Vector2(0.03, 0.016); // metres at the edge of the frame
const ease = "power3.inOut";

/**
 * Restricted camera. The 3D camera is always exactly one of the two Blender
 * cameras (or a blend while moving between them), shifted by a few
 * centimetres for the parallax. Zoom crops the frame (view offset), the only
 * zoom that keeps the live product registered with the stills.
 *
 * Room -> product reads as one move (a match cut): both stills are scaled so
 * the product keeps one place and size while it grows from its room framing to
 * its product framing, and the stills dissolve underneath; the live product
 * takes over once the camera has arrived.
 */
export function ShotRig({ room, orient }: { room: RoomId; orient: Orientation }) {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  const size = useThree((s) => s.size);
  const view = useShowroom((s) => s.view);
  const exploded = useShowroom((s) => s.exploded);
  const hovered = useShowroom((s) => s.hovered);
  const reduced = useShowroom((s) => s.reducedMotion);
  const finish = useShowroom((s) => s.finishes[ROOM_MAP[room].productId]);
  const focus = useMemo(() => productFocus(room, orient), [room, orient]);

  const poses = useMemo(() => {
    const cams = sceneCameras(room, orient);
    const pose = (c: typeof cams.room) => ({
      pos: new THREE.Vector3(...c.position),
      quat: new THREE.Quaternion(...c.quaternion),
      fov: c.fov,
    });
    return { room: pose(cams.room), product: pose(cams.product) };
  }, [room, orient]);

  const pointer = useRef(new THREE.Vector2());
  const zoom = useRef(1);
  const tmp = useMemo(() => ({ pos: new THREE.Vector3(), quat: new THREE.Quaternion(), off: new THREE.Vector3() }), []);
  const k = reduced ? 0.35 : 1; // duration scale

  useEffect(() => {
    camera.layers.enable(IMAGE_LAYER);
    camera.near = 0.05;
    camera.far = 60;
  }, [camera]);

  // New room: start on its establishing shot.
  useEffect(() => {
    gsap.killTweensOf(runtime);
    const s = useShowroom.getState();
    Object.assign(runtime, {
      shot: 0,
      explode: 0,
      rotation: 0,
      rotationTarget: 0,
      hover: 0,
      live: s.finishes[ROOM_MAP[room].productId] === "signature" ? 0 : 1,
    });
    runtime.focusRoom.copy(focus.room);
  }, [room, focus]);

  // Room <-> product.
  useEffect(() => {
    const roomLive = useShowroom.getState().finishes[ROOM_MAP[room].productId] === "signature" ? 0 : 1;
    const tl = gsap.timeline();
    if (view === "product") {
      tl.to(runtime, { live: 0, duration: 0.35 * k, ease: "power1.out" })
        .to(runtime, { shot: 1, duration: 1.9 * k, ease }, 0)
        .to(runtime, { live: 1, duration: 0.8 * k, ease: "power1.inOut" }, ">-0.15");
    } else {
      runtime.rotationTarget = Math.round(runtime.rotation / (Math.PI * 2)) * Math.PI * 2;
      tl.to(runtime, { explode: 0, duration: 0.7 * k, ease })
        .to(runtime, { live: 0, duration: 0.45 * k, ease: "power1.inOut" }, 0.2 * k)
        .to(runtime, { shot: 0, duration: 1.9 * k, ease }, ">-0.05")
        .to(runtime, { live: roomLive, duration: 0.5 * k, ease: "power1.inOut" });
    }
    return () => {
      tl.kill();
    };
  }, [view, room, k]);

  // Finish changed while in the room view (back from the product view).
  useEffect(() => {
    if (useShowroom.getState().view !== "room") return;
    gsap.to(runtime, { live: finish === "signature" ? 0 : 1, duration: 0.6 * k });
  }, [finish, k]);

  useEffect(() => {
    gsap.to(runtime, { explode: exploded ? 1 : 0, duration: 1.6 * k, ease: "power2.inOut" });
  }, [exploded, k]);

  useEffect(() => {
    gsap.to(runtime, { hover: hovered && !reduced ? 1 : 0, duration: 0.9, ease: "power2.out" });
  }, [hovered, reduced]);

  // Mouse parallax (desktop pointers only).
  useEffect(() => {
    const move = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      pointer.current.set((e.clientX / window.innerWidth) * 2 - 1, -((e.clientY / window.innerHeight) * 2 - 1));
    };
    window.addEventListener("pointermove", move);
    return () => window.removeEventListener("pointermove", move);
  }, []);

  useFrame((state, dt) => {
    const damp = 1 - Math.exp(-dt * 2.5);
    const s = runtime.shot;
    const { pos, quat, off } = tmp;
    pos.lerpVectors(poses.room.pos, poses.product.pos, s);
    quat.slerpQuaternions(poses.room.quat, poses.product.quat, s);
    const fov = THREE.MathUtils.lerp(poses.room.fov, poses.product.fov, s);

    // parallax: mouse + a slow breath, damped; off when motion is reduced
    const t = state.clock.elapsedTime;
    const motion = reduced ? 0 : 1 / zoom.current;
    const tx = (pointer.current.x * PARALLAX.x + Math.sin(t * 0.21) * 0.004) * motion;
    const ty = (pointer.current.y * PARALLAX.y + Math.sin(t * 0.17) * 0.003) * motion;
    runtime.parallax.x += (tx - runtime.parallax.x) * damp;
    runtime.parallax.y += (ty - runtime.parallax.y) * damp;
    off.set(runtime.parallax.x, runtime.parallax.y, 0).applyQuaternion(quat);

    camera.position.copy(pos).add(off);
    camera.quaternion.copy(quat);
    camera.fov = fov;
    camera.aspect = size.width / Math.max(size.height, 1);

    // crops: the match cut while moving, the user zoom once in the product shot
    zoom.current += (useShowroom.getState().zoom - zoom.current) * (1 - Math.exp(-dt * 6));
    if (s > 0.999) {
      runtime.cropRoom.set(0, 0, 1, 1);
      cropAround(focus.product, zoom.current, runtime.cropProduct);
    } else if (s < 0.001 || reduced) {
      runtime.cropRoom.set(0, 0, 1, 1);
      runtime.cropProduct.set(0, 0, 1, 1);
    } else {
      matchCrops(focus, s, runtime.cropRoom, runtime.cropProduct);
    }

    // the 3D camera follows the crop of the shot it is in (it is only seen at rest)
    const c = s > 0.5 ? runtime.cropProduct : runtime.cropRoom;
    if (c.z < 0.999) {
      camera.setViewOffset(size.width, size.height, c.x * size.width, (1 - c.y - c.w) * size.height, c.z * size.width, c.w * size.height);
    } else {
      camera.clearViewOffset();
    }
    camera.updateProjectionMatrix();

    // turntable
    runtime.rotation += (runtime.rotationTarget - runtime.rotation) * (1 - Math.exp(-dt * 5));
  });

  return null;
}
