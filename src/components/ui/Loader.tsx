"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { useProgress } from "@react-three/drei";
import { SITE } from "@/config/site";
import { useShowroom } from "@/lib/store";

const MIN_DURATION = 1.8; // seconds — enough for the brand moment, never longer

/**
 * Branded loading screen. Follows real asset progress (GLB / texture loaders
 * via drei's useProgress), waits for the scene's first rendered frames, then
 * lifts away and hands over to the intro camera move.
 */
export function Loader() {
  const sceneReady = useShowroom((s) => s.sceneReady);
  const enter = useShowroom((s) => s.enter);
  const { progress, active } = useProgress();
  const root = useRef<HTMLDivElement>(null);
  const bar = useRef<HTMLDivElement>(null);
  const shown = useRef({ v: 0 });
  const real = useRef(0);
  const started = useRef(0);
  const leaving = useRef(false);
  const [pct, setPct] = useState(0);
  const [gone, setGone] = useState(false);

  real.current = active ? progress / 100 : 0;

  const paint = () => {
    const v = Math.max(shown.current.v, real.current * 0.86);
    if (bar.current) bar.current.style.transform = `scaleX(${v})`;
    setPct(Math.round(v * 100));
  };

  // Crawl towards 86% while the scene compiles.
  useEffect(() => {
    started.current = performance.now();
    const t = gsap.to(shown.current, { v: 0.86, duration: MIN_DURATION * 1.3, ease: "power1.out", onUpdate: paint });
    return () => {
      t.kill();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Complete and exit once the scene has rendered and nothing is still loading.
  useEffect(() => {
    if (!sceneReady || active || leaving.current) return;
    leaving.current = true;
    const elapsed = (performance.now() - started.current) / 1000;
    const tl = gsap.timeline({ onComplete: () => setGone(true) });
    tl.to(shown.current, { v: 1, duration: Math.max(0.5, MIN_DURATION - elapsed), ease: "power2.inOut", onUpdate: paint })
      .to(root.current!.querySelectorAll("[data-fade]"), { opacity: 0, y: -8, duration: 0.6, stagger: 0.06, ease: "power2.in" }, "+=0.15")
      .add(enter, "-=0.2")
      .to(root.current, { opacity: 0, duration: 1.1, ease: "power2.inOut" }, "-=0.1");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sceneReady, active, enter]);

  if (gone) return null;

  return (
    <div
      ref={root}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-ivory text-charcoal"
      role="status"
      aria-live="polite"
      aria-label="Loading the showroom"
    >
      <div className="flex flex-col items-center gap-3" data-fade>
        <span className="pl-[0.62em] text-[13px] font-medium tracking-[0.62em]">{SITE.brand}</span>
        <span className="eyebrow text-stone">{SITE.descriptor}</span>
      </div>
      <div className="mt-14 w-[min(240px,60vw)]" data-fade>
        <div className="h-px w-full overflow-hidden bg-charcoal/10">
          <div ref={bar} className="h-full w-full origin-left scale-x-0 bg-charcoal" />
        </div>
        <div className="mt-3 flex justify-between text-[10.5px] tracking-[0.18em] text-stone tabular-nums">
          <span>PREPARING THE ROOM</span>
          <span>{String(pct).padStart(3, "0")}</span>
        </div>
      </div>
    </div>
  );
}
