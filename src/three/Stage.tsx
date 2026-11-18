"use client";

import { Suspense, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, PerformanceMonitor, useGLTF } from "@react-three/drei";
import { PRODUCTS } from "@/config/products";
import { Orientation, ROOMS, ROOM_MAP, RoomId, Shot, aspectOf, hasPortrait, probeUrl, roomAsset } from "@/config/rooms";
import { useShowroom } from "@/lib/store";
import { preloadMaterials } from "./materials";
import { Backdrop, preloadRoom } from "./stage/Backdrop";
import { LiveProduct } from "./stage/LiveProduct";
import { ShotRig } from "./stage/ShotRig";
import { runtime } from "./stage/runtime";
import { productFocus } from "./stage/focus";

const PANEL_W = 420; // desktop product panel width (px), see ProductPanel
const DISSOLVE_MS = 900;

type FrameBox = { room: RoomId; shot: Shot; orient: Orientation; left: number; top: number; fw: number; fh: number };

/** Flags the stage as ready once a few frames of the current room rendered. */
function ReadySignal({ room }: { room: RoomId }) {
  const setSceneReady = useShowroom((s) => s.setSceneReady);
  const frames = useRef(0);
  useEffect(() => {
    frames.current = 0;
  }, [room]);
  useFrame(() => {
    frames.current++;
    if (frames.current === 4) setSceneReady(true);
  });
  return null;
}

/**
 * The stage: a 16:9 frame (the Cycles stills' frame) that covers the
 * viewport, holding one WebGL canvas: plate, live product, beauty still.
 * On narrow screens the frame slides so the product stays in view; in the
 * product view on desktop it slides left of the product panel.
 */
export default function Stage() {
  const room = useShowroom((s) => s.room);
  const view = useShowroom((s) => s.view);
  const quality = useShowroom((s) => s.quality);
  const entered = useShowroom((s) => s.entered);
  const finishSwitch = useShowroom((s) => s.finishSwitch);
  const sceneReady = useShowroom((s) => s.sceneReady);
  const reduced = useShowroom((s) => s.reducedMotion);
  const selected = useShowroom((s) => s.selected);
  const [shown, setShown] = useState<RoomId>(room);
  // the product whose camera is the product view (valid for the room on screen)
  const shotProduct = ROOM_MAP[shown].productIds.includes(selected) ? selected : ROOM_MAP[shown].productIds[0];
  /** The previous room's still, dissolving over the new one. */
  const [ghost, setGhost] = useState<(FrameBox & { on: boolean }) | null>(null);
  /** The frame sits a little closer, then settles (entry and new room). */
  const [settle, setSettle] = useState(true);
  const [vp, setVp] = useState({ w: 1600, h: 900 });
  const frameRef = useRef<HTMLDivElement>(null);
  // resolution budget: starts at the device quality, steps down if frames drop
  const maxDpr = quality === "high" ? 2 : 1.5;
  const [dpr, setDpr] = useState(maxDpr);
  useEffect(() => setDpr(maxDpr), [maxDpr]);
  const lastBox = useRef<FrameBox | null>(null);
  // phones held upright get the 9:16 stills (rendered for them), others the 16:9 ones
  const orient: Orientation = vp.w / vp.h < 0.8 && hasPortrait(shown) ? "portrait" : "landscape";
  const aspect = aspectOf(orient);
  const f2 = productFocus(shown, orient, shotProduct);
  const focus = { room: { x: f2.room.x, y: 1 - f2.room.y }, product: { x: f2.product.x, y: 1 - f2.product.y } };

  // viewport
  useLayoutEffect(() => {
    const read = () => setVp({ w: window.innerWidth, h: window.innerHeight });
    read();
    window.addEventListener("resize", read);
    return () => window.removeEventListener("resize", read);
  }, []);

  // assets: the other rooms and all models, once the first room is up
  useEffect(() => {
    preloadMaterials();
    if (!entered) return;
    ROOMS.forEach((r) => preloadRoom(r.id, orient));
    PRODUCTS.forEach((p) => useGLTF.preload(p.model));
  }, [entered, orient]);

  // entry: settle once the loader hands over
  useEffect(() => {
    if (entered) requestAnimationFrame(() => setSettle(false));
  }, [entered, orient]);

  // room switch: freeze the old still over the stage, swap underneath, dissolve
  useEffect(() => {
    if (room === shown) return;
    if (lastBox.current) setGhost({ ...lastBox.current, on: true });
    useShowroom.getState().setSceneReady(false);
    setSettle(true);
    setShown(room);
  }, [room, shown]);
  const ghostOn = ghost?.on;
  useEffect(() => {
    if (!ghostOn || room !== shown || !sceneReady) return;
    const t = setTimeout(() => {
      setGhost((g) => (g ? { ...g, on: false } : g));
      setSettle(false);
    }, 120);
    return () => clearTimeout(t);
  }, [ghostOn, room, shown, sceneReady]);
  useEffect(() => {
    if (ghostOn !== false) return;
    const t = setTimeout(() => {
      setGhost(null);
      finishSwitch();
    }, reduced ? 300 : DISSOLVE_MS);
    return () => clearTimeout(t);
  }, [ghostOn, reduced, finishSwitch]);
  // no previous still to dissolve from (first switch before entry): just finish
  useEffect(() => {
    if (room === shown && !ghost && useShowroom.getState().switching && sceneReady) finishSwitch();
  }, [room, shown, ghost, sceneReady, finishSwitch]);

  // frame geometry
  const desktop = vp.w >= 1024;
  const portrait = vp.w / vp.h < 1;
  const f = view === "product" ? focus.product : focus.room;
  const visibleW = view === "product" && desktop ? vp.w - PANEL_W : vp.w;
  // mobile: the product sheet covers the lower 45 %; in the room view the copy
  // sits low, so the product is framed in the upper part of the screen
  const visibleH = desktop ? vp.h : view === "product" ? vp.h * 0.55 : portrait ? vp.h * 0.6 : vp.h;
  // the frame only has to cover what is visible (the sheet hides the rest)
  const coverH = view === "product" && !desktop ? visibleH : vp.h;
  const fw = Math.max(vp.w, coverH * aspect);
  const fh = fw / aspect;
  const left = THREE.MathUtils.clamp(visibleW / 2 - f.x * fw, Math.min(0, visibleW - fw), 0);
  const top = THREE.MathUtils.clamp(visibleH / 2 - f.y * fh, Math.min(0, coverH - fh), 0);
  useLayoutEffect(() => {
    if (room === shown) lastBox.current = { room: shown, shot: view === "room" ? "room" : shotProduct, orient, left, top, fw, fh };
  });

  // drag to turn, wheel / pinch to zoom (product view only)
  useEffect(() => {
    const el = frameRef.current;
    if (!el) return;
    const pointers = new Map<number, { x: number; y: number }>();
    let pinch = 0;
    let swipe: { x: number; y: number; id: number } | null = null;
    const isProduct = () => useShowroom.getState().view === "product" && !useShowroom.getState().switching;
    const down = (e: PointerEvent) => {
      // room view, touch: horizontal swipe changes room
      if (!isProduct() && e.pointerType !== "mouse") swipe = { x: e.clientX, y: e.clientY, id: e.pointerId };
      if (!isProduct()) return;
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()];
        pinch = Math.hypot(a.x - b.x, a.y - b.y);
      }
    };
    const move = (e: PointerEvent) => {
      const prev = pointers.get(e.pointerId);
      if (!prev || !isProduct()) return;
      if (pointers.size === 1) {
        runtime.rotationTarget += ((e.clientX - prev.x) / Math.max(el.clientWidth, 1)) * Math.PI * 2.4;
      }
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (pinch > 0) {
          const s = useShowroom.getState();
          s.setZoom(s.zoom * (d / pinch));
        }
        pinch = d;
      }
    };
    const up = (e: PointerEvent) => {
      if (swipe && swipe.id === e.pointerId) {
        const dx = e.clientX - swipe.x;
        const dy = e.clientY - swipe.y;
        const s = useShowroom.getState();
        if (Math.abs(dx) > 70 && Math.abs(dy) < 60 && s.view === "room" && !s.switching) s.nextRoom(dx < 0 ? 1 : -1);
        swipe = null;
      }
      pointers.delete(e.pointerId);
      if (pointers.size < 2) pinch = 0;
    };
    const wheel = (e: WheelEvent) => {
      if (!isProduct()) return;
      e.preventDefault();
      const s = useShowroom.getState();
      s.setZoom(s.zoom * Math.exp(-e.deltaY * 0.0015));
    };
    el.addEventListener("pointerdown", down);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    window.addEventListener("pointercancel", up);
    el.addEventListener("wheel", wheel, { passive: false });
    return () => {
      el.removeEventListener("pointerdown", down);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("pointercancel", up);
      el.removeEventListener("wheel", wheel);
    };
  }, []);

  // keyboard: arrows change room (room view) or turn the piece (product view), Esc goes back
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
      const s = useShowroom.getState();
      if (!s.entered || s.switching) return;
      if (s.view === "product") {
        if (e.key === "Escape") s.backToRoom();
        else if (e.key === "ArrowLeft") runtime.rotationTarget -= Math.PI / 6;
        else if (e.key === "ArrowRight") runtime.rotationTarget += Math.PI / 6;
        else if (e.key === "+" || e.key === "=") s.setZoom(s.zoom * 1.3);
        else if (e.key === "-") s.setZoom(s.zoom / 1.3);
        else return;
      } else {
        if (e.key === "ArrowRight") s.nextRoom(1);
        else if (e.key === "ArrowLeft") s.nextRoom(-1);
        else return;
      }
      e.preventDefault();
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);

  const exposure = Math.pow(2, ROOM_MAP[shown].exposure);

  return (
    <div className="absolute inset-0 overflow-hidden bg-ivory">
      <div
        ref={frameRef}
        data-product={view === "product" || undefined}
        className="absolute transition-transform duration-[1600ms] ease-[var(--ease-cine)] data-product:cursor-grab data-product:active:cursor-grabbing"
        style={{ width: fw, height: fh, transform: `translate3d(${left}px, ${top}px, 0)`, touchAction: "none" }}
      >
        <div
          className="absolute inset-0 origin-center"
          style={{
            transform: settle && !reduced ? "scale(1.045)" : "none",
            transition: settle ? "none" : "transform 2600ms cubic-bezier(0.22, 0.61, 0.24, 1)",
          }}
        >
        <Canvas
          dpr={Math.min(dpr, typeof window === "undefined" ? 1 : window.devicePixelRatio)}
          camera={{ fov: 40, near: 0.05, far: 60, position: [0, 1.5, 4] }}
          gl={{ antialias: true, powerPreference: "high-performance" }}
          onCreated={({ gl }) => {
            gl.toneMapping = THREE.AgXToneMapping;
          }}
        >
          <ToneExposure value={exposure} />
          <PerformanceMonitor
            onDecline={() => setDpr((d) => Math.max(1, d - 0.25))}
            onIncline={() => setDpr((d) => Math.min(maxDpr, d + 0.25))}
            flipflops={3}
            onFallback={() => setDpr(1)}
          />
          <Suspense fallback={null}>
            <Environment files={probeUrl(shown, shotProduct)} environmentIntensity={1} />
            <Backdrop room={shown} kind="plate" orient={orient} product={shotProduct} />
            {ROOM_MAP[shown].productIds.map((id) => (
              <LiveProduct key={id} room={shown} productId={id} />
            ))}
            <Backdrop room={shown} kind="beauty" orient={orient} product={shotProduct} />
            <ReadySignal room={shown} />
          </Suspense>
          <ShotRig room={shown} orient={orient} product={shotProduct} />
        </Canvas>
        </div>
      </div>
      {ghost && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={roomAsset(ghost.room, ghost.shot, "beauty", ghost.orient)}
          alt=""
          aria-hidden
          className="pointer-events-none absolute max-w-none ease-[var(--ease-cine)]"
          style={{
            left: 0,
            top: 0,
            width: ghost.fw,
            height: ghost.fh,
            transform: `translate3d(${ghost.left}px, ${ghost.top}px, 0) scale(${ghost.on ? 1 : 1.03})`,
            opacity: ghost.on ? 1 : 0,
            transitionProperty: "opacity, transform",
            transitionDuration: ghost.on ? "0ms" : `${reduced ? 300 : DISSOLVE_MS}ms`,
          }}
        />
      )}
    </div>
  );
}

function ToneExposure({ value }: { value: number }) {
  useFrame(({ gl }) => {
    gl.toneMappingExposure = value;
  });
  return null;
}
