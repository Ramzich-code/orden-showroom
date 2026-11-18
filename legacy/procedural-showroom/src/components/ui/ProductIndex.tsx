"use client";

import { PRODUCTS, getFinish } from "@/config/products";
import { useShowroom } from "@/lib/store";

/**
 * Text index of the pieces in the room. Hovering an entry highlights the
 * piece in 3D (and vice versa), so the list and the room read as one.
 */
export function ProductIndex() {
  const visible = useShowroom((s) => s.entered && s.view === "showroom");
  const hoveredId = useShowroom((s) => s.hoveredId);
  const finishes = useShowroom((s) => s.finishes);
  const setHovered = useShowroom((s) => s.setHovered);

  return (
    <nav
      aria-label="Pieces in this room"
      data-on={visible || undefined}
      className="group pointer-events-none absolute inset-x-0 bottom-0 z-10 px-5 pb-5 md:inset-x-auto md:right-10 md:bottom-12 md:w-[300px] md:px-0 md:pb-0"
    >
      <div
        className="mb-3 hidden translate-y-3 opacity-0 transition-[opacity,transform] delay-[1600ms] duration-[1200ms] ease-[var(--ease-cine)] group-data-on:translate-y-0 group-data-on:opacity-100 md:block"
      >
        <span className="eyebrow text-charcoal/60">In this room</span>
      </div>
      <ol className="flex gap-2 overflow-x-auto [scrollbar-width:none] md:flex-col md:gap-0 md:overflow-visible md:border-t md:border-charcoal/15">
        {PRODUCTS.map((p, i) => {
          const finish = getFinish(p, finishes[p.id]);
          const active = hoveredId === p.id;
          return (
            <li
              key={p.id}
              style={{ transitionDelay: visible ? `${1700 + i * 120}ms` : "0ms" }}
              className="min-w-[148px] flex-1 translate-y-3 opacity-0 transition-[opacity,transform] duration-[1100ms] ease-[var(--ease-cine)] group-data-on:pointer-events-auto group-data-on:translate-y-0 group-data-on:opacity-100 md:min-w-0"
            >
              <div
                onPointerEnter={() => setHovered(p.id)}
                onPointerLeave={() => useShowroom.getState().hoveredId === p.id && setHovered(null)}
                data-active={active || undefined}
                className="group/item flex h-full cursor-pointer flex-col gap-1 border border-charcoal/10 bg-paper/80 px-3 py-2.5 backdrop-blur-md transition-colors duration-500 data-active:bg-paper md:flex-row md:items-center md:gap-4 md:border-0 md:border-b md:border-charcoal/15 md:bg-transparent md:px-0 md:py-4 md:backdrop-blur-none md:data-active:bg-transparent"
              >
                <span className="text-[10px] tracking-[0.18em] text-stone tabular-nums">{p.index}</span>
                <span className="flex-1 text-[13px] leading-tight text-ink transition-transform duration-500 ease-[var(--ease-cine)] md:group-data-active/item:translate-x-1.5">
                  {p.name}
                </span>
                <span className="flex items-center gap-2 text-[11px] text-charcoal/60">
                  <span
                    className="h-2.5 w-2.5 rounded-full ring-1 ring-charcoal/15"
                    style={{ background: finish.swatch }}
                    aria-hidden
                  />
                  {finish.name}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
