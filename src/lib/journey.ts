"use client";

import { create } from "zustand";
import { JOURNEY, JOURNEY_LENGTH } from "@/config/journey";

/** Scroll state of the journey (written by ScrollJourney, read everywhere). */
interface JourneyState {
  /** Scroll position in viewport heights. */
  y: number;
  /** Current step and progress inside it (0..1). */
  step: number;
  local: number;
  /** 0..1 over the whole journey. */
  progress: number;
  /** Opacity of the frame sequence over the stage (1 = covers the live room). */
  cover: number;
  /** The first frames of the opening sequence are loaded. */
  ready: boolean;
  set: (p: Partial<JourneyState>) => void;
}

export const useJourney = create<JourneyState>((set) => ({
  y: 0,
  step: 0,
  local: 0,
  progress: 0,
  cover: 1,
  ready: false,
  set: (p) => set(p),
}));

/** Where scroll position y (viewport heights) falls on the journey. */
export function locate(y: number) {
  let acc = 0;
  for (let i = 0; i < JOURNEY.length; i++) {
    const len = JOURNEY[i].length;
    if (y < acc + len || i === JOURNEY.length - 1) {
      return { step: i, local: Math.min(1, Math.max(0, (y - acc) / len)), progress: Math.min(1, y / JOURNEY_LENGTH) };
    }
    acc += len;
  }
  return { step: 0, local: 0, progress: 0 };
}

/** Scrolls the page to a position in viewport heights. */
export function scrollToVh(vh: number, smooth = true) {
  window.scrollTo({ top: vh * window.innerHeight, behavior: smooth ? "smooth" : "auto" });
}
