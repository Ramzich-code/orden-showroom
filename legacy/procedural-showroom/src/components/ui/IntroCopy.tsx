"use client";

import { SITE } from "@/config/site";
import { useShowroom } from "@/lib/store";

/** The opening statement. Staggers in after the loader, hides when a product is in focus. */
export function IntroCopy() {
  const visible = useShowroom((s) => s.entered && s.view === "showroom");
  const reveal = (delay: number) => ({
    className:
      "block translate-y-4 opacity-0 transition-[opacity,transform] duration-[1200ms] ease-[var(--ease-cine)] group-data-on:translate-y-0 group-data-on:opacity-100",
    style: { transitionDelay: visible ? `${delay}ms` : "0ms" },
  });

  return (
    <section
      data-on={visible || undefined}
      className="group pointer-events-none absolute left-5 top-24 z-10 max-w-[30rem] md:bottom-12 md:left-10 md:top-auto"
    >
      <span {...reveal(900)}>
        <span className="eyebrow text-charcoal/70">Collection 2026 — Living &amp; Rest</span>
      </span>
      <h1 className="mt-3 font-display text-[44px] leading-[0.95] tracking-[-0.01em] text-ink md:mt-5 md:text-[clamp(56px,6.4vw,104px)]">
        <span {...reveal(1050)}>Designed</span>
        <span {...reveal(1200)}>
          to <em className="italic">belong.</em>
        </span>
      </h1>
      <span {...reveal(1500)}>
        <p className="mt-4 max-w-[22rem] text-[13.5px] leading-relaxed text-charcoal/75 md:mt-6 md:text-[14.5px]">
          Three pieces, one room. Step inside and choose a piece to see it up close, in oak, white or black.
        </p>
      </span>
      <span {...reveal(1750)}>
        <span className="mt-4 flex items-center gap-3 text-[11.5px] tracking-[0.04em] text-charcoal/60 md:mt-6">
          <DragIcon />
          Drag to look around
        </span>
      </span>
      <span className="sr-only">{SITE.tagline}</span>
    </section>
  );
}

function DragIcon() {
  return (
    <svg width="26" height="12" viewBox="0 0 26 12" fill="none" aria-hidden>
      <path d="M1 6h24M5 2 1 6l4 4M21 2l4 4-4 4" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}
