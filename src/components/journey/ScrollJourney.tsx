"use client";

import { useEffect } from "react";
import { JOURNEY, JOURNEY_LENGTH } from "@/config/journey";
import { ROOMS } from "@/config/rooms";
import { locate, useJourney } from "@/lib/journey";
import { useShowroom } from "@/lib/store";

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/**
 * Drives the journey from the page scroll: which step we are in, how far, how
 * much the frame sequence covers the live room, and which room the live stage
 * shows (switched only while the frames cover it). The page itself is only a
 * tall spacer; everything on screen is fixed.
 */
export function ScrollJourney() {
  const view = useShowroom((s) => s.view);
  const entered = useShowroom((s) => s.entered);

  // no scrolling while a piece is open, nor behind the loader
  useEffect(() => {
    const lock = view === "product" || !entered;
    document.documentElement.style.overflow = lock ? "hidden" : "";
    return () => {
      document.documentElement.style.overflow = "";
    };
  }, [view, entered]);

  useEffect(() => {
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    let raf = 0;
    const update = () => {
      raf = 0;
      const y = window.scrollY / Math.max(1, window.innerHeight);
      const { step, local, progress } = locate(y);
      const s = JOURNEY[step];
      let cover = 0;
      if (s.kind === "glide") {
        // room glides fade in from the previous room and hand over to the live room at the end
        cover = s.segment === "exterior" ? 1 : smooth(0, 0.06, local) * (1 - smooth(0.9, 0.99, local));
      }
      useJourney.getState().set({ y, step, local, progress, cover });
      // the live stage follows the journey, switching only behind the frames
      const room = s.room ?? (s.kind === "finale" ? ROOMS[ROOMS.length - 1].id : ROOMS[0].id);
      const sr = useShowroom.getState();
      if (room !== sr.room && (cover > 0.99 || s.segment === "exterior")) sr.enterRoomCovered(room);
      if (s.kind !== "rest" && sr.hovered) sr.setHovered(null);
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return <div aria-hidden style={{ height: `${(JOURNEY_LENGTH + 1) * 100}vh` }} />;
}
