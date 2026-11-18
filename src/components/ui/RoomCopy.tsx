"use client";

import { PRODUCT_MAP, getFinish } from "@/config/products";
import { ROOM_MAP } from "@/config/rooms";
import { SITE } from "@/config/site";
import { useShowroom } from "@/lib/store";

/** Room view copy: the room, its piece, and the way in to the product. */
export function RoomCopy() {
  const room = useShowroom((s) => ROOM_MAP[s.room]);
  const visible = useShowroom((s) => s.entered && s.view === "room" && !s.switching);
  const hovered = useShowroom((s) => s.hovered);
  const finish = useShowroom((s) => s.finishes[ROOM_MAP[s.room].productId]);
  const setHovered = useShowroom((s) => s.setHovered);
  const openProduct = useShowroom((s) => s.openProduct);
  const product = PRODUCT_MAP[room.productId];
  const f = getFinish(product, finish);

  const reveal = (delay: number) => ({
    className:
      "block translate-y-4 opacity-0 transition-[opacity,transform] duration-[1100ms] ease-[var(--ease-cine)] group-data-on:translate-y-0 group-data-on:opacity-100",
    style: { transitionDelay: visible ? `${delay}ms` : "0ms" },
  });

  return (
    <section
      key={room.id}
      data-on={visible || undefined}
      className="group pointer-events-none absolute inset-x-5 bottom-[76px] z-20 md:inset-x-10 md:bottom-12 md:flex md:items-end md:justify-between md:gap-10"
    >
      <div className="max-w-[34rem]">
        <span {...reveal(150)}>
          <span className="eyebrow text-charcoal/70">
            Room {room.index} · {SITE.tagline}
          </span>
        </span>
        <h1 className="mt-3 font-display text-[46px] leading-[0.92] tracking-[-0.01em] text-ink md:mt-4 md:text-[clamp(60px,6.6vw,108px)]">
          <span {...reveal(260)}>{room.title}</span>
        </h1>
        <span {...reveal(420)}>
          <p className="mt-3 text-[13.5px] leading-relaxed text-charcoal/75 md:mt-4 md:text-[14.5px]">{room.mood}</p>
        </span>
      </div>

      <span {...reveal(560)}>
        <button
          type="button"
          onClick={openProduct}
          onPointerEnter={() => setHovered(true)}
          onPointerLeave={() => setHovered(false)}
          data-active={hovered || undefined}
          className="group/card pointer-events-auto mt-5 flex w-full items-center gap-4 border border-charcoal/10 bg-paper/80 px-4 py-3.5 text-left backdrop-blur-md transition-colors duration-500 hover:bg-paper data-active:bg-paper md:mt-0 md:w-[340px]"
        >
          <span className="text-[10px] tracking-[0.18em] text-stone tabular-nums">{product.index}</span>
          <span className="flex flex-1 flex-col gap-1">
            <span className="text-[14px] leading-tight text-ink">{product.name}</span>
            <span className="flex items-center gap-2 text-[11.5px] text-charcoal/60">
              <span className="h-2.5 w-2.5 rounded-full ring-1 ring-charcoal/15" style={{ background: f.swatch }} aria-hidden />
              {f.name}
            </span>
          </span>
          <span className="eyebrow flex items-center gap-2 text-ink">
            Discover
            <Arrow />
          </span>
        </button>
      </span>
    </section>
  );
}

function Arrow() {
  return (
    <svg width="18" height="10" viewBox="0 0 18 10" fill="none" aria-hidden className="transition-transform duration-500 group-hover/card:translate-x-1">
      <path d="M0 5h16M12 1l4 4-4 4" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}
