"use client";

import { useEffect, useRef } from "react";
import { JOURNEY, SegmentId, frameCount, frameUrl } from "@/config/journey";
import { useJourney } from "@/lib/journey";
import { useShowroom } from "@/lib/store";

const cache = new Map<string, HTMLImageElement>();

function load(url: string, onload?: () => void) {
  let img = cache.get(url);
  if (!img) {
    img = new Image();
    img.decoding = "async";
    img.src = url;
    cache.set(url, img);
  }
  if (onload) {
    if (img.complete && img.naturalWidth) onload();
    else img.addEventListener("load", onload, { once: true });
  }
  return img;
}

function preloadSegment(segment: SegmentId, portrait: boolean, onFirst?: () => void) {
  const n = frameCount(segment, portrait);
  let loaded = 0;
  const first = Math.min(12, n);
  for (let i = 0; i < n; i++)
    load(frameUrl(segment, portrait, i), () => {
      loaded++;
      if (loaded === first) onFirst?.();
    });
}

/**
 * The Cycles frame sequence of the current glide, scrubbed by the scroll and
 * drawn over the stage (same 16:9 / 9:16 frame, so the last frame of a room
 * glide sits exactly on the live room underneath). Neighbouring frames are
 * blended, so slow scrolling stays smooth.
 */
export function JourneyFrames({ portrait }: { portrait: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const entered = useShowroom((s) => s.entered);

  // opening sequence first; the room glides once the house is on screen
  useEffect(() => {
    preloadSegment("exterior", portrait, () => useJourney.getState().set({ ready: true }));
    if (frameCount("exterior", portrait) === 0) useJourney.getState().set({ ready: true });
  }, [portrait]);
  useEffect(() => {
    if (!entered) return;
    for (const s of ["living", "bedroom", "storage"] as const) preloadSegment(s, portrait);
  }, [entered, portrait]);

  useEffect(() => {
    let raf = 0;
    let last = "";
    const draw = () => {
      raf = requestAnimationFrame(draw);
      const c = canvas.current;
      if (!c) return;
      const { step, local, cover } = useJourney.getState();
      c.style.opacity = String(cover);
      const s = JOURNEY[step];
      if (s.kind !== "glide" || !s.segment || cover <= 0.001) return;
      const n = frameCount(s.segment, portrait);
      if (!n) return;
      const w = Math.round(c.clientWidth * Math.min(1.5, window.devicePixelRatio || 1));
      const h = Math.round(c.clientHeight * Math.min(1.5, window.devicePixelRatio || 1));
      if (c.width !== w || c.height !== h) {
        c.width = w;
        c.height = h;
        last = "";
      }
      const f = local * (n - 1);
      const i0 = Math.floor(f);
      const i1 = Math.min(n - 1, i0 + 1);
      const t = f - i0;
      const key = `${s.segment}:${portrait}:${f.toFixed(3)}:${w}x${h}`;
      if (key === last) return;
      const a = load(frameUrl(s.segment, portrait, i0));
      const b = load(frameUrl(s.segment, portrait, i1));
      const ctx = c.getContext("2d")!;
      if (!a.complete || !a.naturalWidth) return; // keep the previous frame until it arrives
      ctx.globalAlpha = 1;
      ctx.drawImage(a, 0, 0, w, h);
      if (t > 0.01 && b.complete && b.naturalWidth) {
        ctx.globalAlpha = t;
        ctx.drawImage(b, 0, 0, w, h);
      }
      last = key;
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [portrait]);

  return <canvas ref={canvas} aria-hidden className="pointer-events-none absolute inset-0 z-10 h-full w-full" />;
}
