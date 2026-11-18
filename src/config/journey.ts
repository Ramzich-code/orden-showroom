/**
 * The scroll journey: the page scrolls through the ORDEN house. Glides are
 * Cycles frame sequences (blender/journey/journey.py) scrubbed by the scroll;
 * every room glide ends exactly on the room's camera, where the interactive
 * room (stills + live pieces) takes over for the "rest" stretch.
 *
 * Lengths are in viewport heights of scroll.
 */
import type { RoomId } from "./rooms";
import manifest from "./journey.json";
import { asset } from "@/config/site";

export type SegmentId = "exterior" | RoomId;

export interface JourneyStep {
  kind: "glide" | "rest" | "finale";
  /** Frame sequence (glides) or room (rest). */
  segment?: SegmentId;
  room?: RoomId;
  length: number;
  /** Headline shown over this step: plain part, then the italic accent. */
  title?: [string, string];
  eyebrow?: string;
}

export const JOURNEY: JourneyStep[] = [
  { kind: "glide", segment: "exterior", length: 2.4, title: ["Designed to", "belong."], eyebrow: "ORDEN · Collection 001" },
  { kind: "glide", segment: "living", room: "living", length: 1.5, title: ["Daylight, wool", "and stone."], eyebrow: "Room 01 · Living" },
  { kind: "rest", room: "living", length: 1.3 },
  { kind: "glide", segment: "bedroom", room: "bedroom", length: 1.5, title: ["Close at hand,", "quiet by nature."], eyebrow: "Room 02 · Bedroom" },
  { kind: "rest", room: "bedroom", length: 1.3 },
  { kind: "glide", segment: "storage", room: "storage", length: 1.5, title: ["A calm volume", "for what you keep."], eyebrow: "Room 03 · Dressing" },
  { kind: "rest", room: "storage", length: 1.3 },
  { kind: "finale", length: 1.4, title: ["Six pieces,", "one house."], eyebrow: "Collection 001" },
];

export const JOURNEY_LENGTH = JOURNEY.reduce((a, s) => a + s.length, 0);

/** Scroll position (in viewport heights) where a step starts. */
export const stepStart = (i: number) => JOURNEY.slice(0, i).reduce((a, s) => a + s.length, 0);

/** Index of the rest step of a room (where its interactive view lives). */
export const restStep = (room: RoomId) => JOURNEY.findIndex((s) => s.kind === "rest" && s.room === room);

type Manifest = Partial<Record<SegmentId, { landscape?: number; portrait?: number }>>;
const frames = manifest as Manifest;

export function frameCount(segment: SegmentId, portrait: boolean): number {
  const f = frames[segment];
  return (portrait ? f?.portrait : f?.landscape) ?? f?.landscape ?? 0;
}

export const hasPortraitFrames = (segment: SegmentId) => !!frames[segment]?.portrait;

export function frameUrl(segment: SegmentId, portrait: boolean, i: number) {
  const dir = portrait && hasPortraitFrames(segment) ? `${segment}-p` : segment;
  return asset(`/journey/${dir}/${String(i + 1).padStart(3, "0")}.webp`);
}
