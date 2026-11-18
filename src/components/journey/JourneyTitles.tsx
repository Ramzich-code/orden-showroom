"use client";

import { JOURNEY } from "@/config/journey";
import { useJourney } from "@/lib/journey";
import { useShowroom } from "@/lib/store";

const fade = (local: number) => {
  const inn = Math.min(1, Math.max(0, (local - 0.06) / 0.18));
  const out = 1 - Math.min(1, Math.max(0, (local - 0.72) / 0.16));
  return Math.min(inn, out);
};

/**
 * The headline of each glide: a plain sans line and an italic serif accent in
 * gold, rising in and out with the scroll.
 */
export function JourneyTitles() {
  const step = useJourney((s) => s.step);
  const local = useJourney((s) => s.local);
  const entered = useShowroom((s) => s.entered);
  const s = JOURNEY[step];
  if (s.kind !== "glide" || !s.title) return null;
  const k = entered ? fade(s.segment === "exterior" ? Math.max(local, 0.25) : local) : 0;
  const light = s.segment === "exterior";

  return (
    <section
      aria-live="polite"
      className="pointer-events-none fixed inset-x-5 top-[28%] z-20 md:inset-x-auto md:left-12 md:top-auto md:bottom-[22%] md:max-w-[44rem]"
      style={{ opacity: k, transform: `translate3d(0, ${(1 - k) * 18}px, 0)` }}
    >
      <span className={`eyebrow ${light ? "text-ivory/85" : "text-charcoal/70"}`}>{s.eyebrow}</span>
      <h2
        className={`mt-3 text-[42px] font-medium leading-[0.98] tracking-[-0.02em] md:text-[clamp(56px,6.2vw,104px)] ${
          light ? "text-ivory [text-shadow:0_2px_30px_rgb(0_0_0/0.35)]" : "text-ink"
        }`}
      >
        {s.title[0]} <em className="font-display font-normal italic text-gold">{s.title[1]}</em>
      </h2>
    </section>
  );
}
