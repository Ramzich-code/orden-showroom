"use client";

import { SITE } from "@/config/site";
import { ROOMS } from "@/config/rooms";
import { useShowroom } from "@/lib/store";

/** Brand and the room selector (top on desktop, bottom bar on mobile). */
export function Header() {
  const entered = useShowroom((s) => s.entered);
  const room = useShowroom((s) => s.room);
  const view = useShowroom((s) => s.view);
  const goToRoom = useShowroom((s) => s.goToRoom);

  const nav = (
    <ol className="flex items-center gap-1 md:gap-2">
      {ROOMS.map((r) => (
        <li key={r.id}>
          <button
            type="button"
            onClick={() => goToRoom(r.id)}
            aria-current={r.id === room ? "page" : undefined}
            className="group/room flex items-baseline gap-2 px-3 py-2 text-[12.5px] text-charcoal/55 transition-colors duration-500 hover:text-ink aria-[current=page]:text-ink"
          >
            <span className="text-[10px] tracking-[0.18em] text-stone tabular-nums">{r.index}</span>
            <span className="relative">
              {r.name}
              <span className="absolute -bottom-1 left-0 h-px w-full origin-left scale-x-0 bg-ink transition-transform duration-700 ease-[var(--ease-cine)] group-aria-[current=page]/room:scale-x-100" />
            </span>
          </button>
        </li>
      ))}
    </ol>
  );

  return (
    <>
      <header
        data-on={entered || undefined}
        className="pointer-events-none absolute inset-x-0 top-0 z-30 flex items-start justify-between px-5 pt-5 opacity-0 transition-opacity duration-[1400ms] ease-[var(--ease-cine)] data-on:opacity-100 md:px-10 md:pt-8"
      >
        <a href="/" className="pointer-events-auto flex flex-col gap-1.5" aria-label={`${SITE.brand} home`}>
          <span className="text-[13px] font-semibold tracking-[0.5em] text-ink">{SITE.brand}</span>
          <span className="eyebrow text-charcoal/70">{SITE.descriptor}</span>
        </a>
        <nav
          aria-label="Rooms"
          className="pointer-events-auto -mt-2 hidden rounded-full bg-paper/70 px-2 backdrop-blur-md md:block"
        >
          {nav}
        </nav>
      </header>

      <nav
        aria-label="Rooms"
        data-on={(entered && view === "room") || undefined}
        className="pointer-events-none absolute inset-x-0 bottom-0 z-30 flex translate-y-full justify-center bg-paper/85 pb-[max(env(safe-area-inset-bottom),6px)] pt-1.5 opacity-0 backdrop-blur-md transition-[opacity,transform] duration-700 ease-[var(--ease-cine)] data-on:pointer-events-auto data-on:translate-y-0 data-on:opacity-100 md:hidden"
      >
        {nav}
      </nav>
    </>
  );
}
