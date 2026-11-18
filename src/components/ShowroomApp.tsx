"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useShowroom } from "@/lib/store";
import { Loader } from "./ui/Loader";
import { Header } from "./ui/Header";
import { RoomCopy } from "./ui/RoomCopy";
import { ProductPanel } from "./ui/ProductPanel";
import { StaticFallback } from "./ui/StaticFallback";

// The WebGL bundle (three, fiber, drei) is split out and loaded on the client only.
const Stage = dynamic(() => import("@/three/Stage"), { ssr: false });

function detectWebGL(): boolean {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

export function ShowroomApp() {
  const [support, setSupport] = useState<"pending" | "webgl" | "none">("pending");
  const setQuality = useShowroom((s) => s.setQuality);
  const setReducedMotion = useShowroom((s) => s.setReducedMotion);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const read = () => setReducedMotion(mq.matches);
    read();
    mq.addEventListener("change", read);
    return () => mq.removeEventListener("change", read);
  }, [setReducedMotion]);

  useEffect(() => {
    const lite =
      window.matchMedia("(pointer: coarse)").matches || window.innerWidth < 768 || (navigator.hardwareConcurrency ?? 8) <= 4;
    setQuality(lite ? "low" : "high");
    setSupport(detectWebGL() ? "webgl" : "none");
  }, [setQuality]);

  if (support === "none") return <StaticFallback />;

  return (
    <main className="fixed inset-0 overflow-hidden bg-ivory">
      {support === "webgl" && <Stage />}

      {/* soft scrims that keep the copy legible over the stills, never intercept input */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-ivory/55 to-transparent" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(80%_55%_at_0%_100%,rgb(244_240_232/0.8),transparent_70%)] md:bg-[radial-gradient(50%_55%_at_0%_100%,rgb(244_240_232/0.7),transparent_75%)]" />

      <Header />
      <RoomCopy />
      <ProductPanel />
      <Loader />
    </main>
  );
}
