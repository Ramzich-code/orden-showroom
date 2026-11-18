"use client";

import { useEffect } from "react";
import { JOURNEY, restStep, stepStart } from "@/config/journey";
import { PRODUCTS, ProductId } from "@/config/products";
import { ROOMS, roomAsset, roomOf } from "@/config/rooms";
import { scrollToVh, useJourney } from "@/lib/journey";
import { useShowroom } from "@/lib/store";

const FINALE = JOURNEY.findIndex((s) => s.kind === "finale");
let pending: ProductId | null = null;

/** Scrolls back to a piece's room, then opens it once the room is live. */
function visit(id: ProductId) {
  pending = id;
  scrollToVh(stepStart(restStep(roomOf(id).id)) + 0.1);
}

/**
 * The closing section, after the reference's "Six ways we build": the whole
 * collection as tilted cards, each leading back to its piece in its room.
 */
export function Finale() {
  const step = useJourney((s) => s.step);
  const local = useJourney((s) => s.local);
  const on = step === FINALE;
  const k = on ? Math.min(1, local / 0.25) : 0;

  // open the piece once the scroll has brought its room back
  useEffect(
    () =>
      useJourney.subscribe((s) => {
        if (!pending) return;
        const st = JOURNEY[s.step];
        const room = roomOf(pending).id;
        if (st.kind === "rest" && st.room === room && useShowroom.getState().room === room && s.cover < 0.01) {
          const id = pending;
          pending = null;
          setTimeout(() => useShowroom.getState().openProduct(id), 350);
        }
      }),
    [],
  );

  return (
    <section
      aria-hidden={!on}
      className="fixed inset-0 z-20 flex flex-col justify-center overflow-hidden bg-ink px-5 md:px-12"
      style={{ opacity: k, pointerEvents: k > 0.5 ? "auto" : "none" }}
    >
      <span className="eyebrow text-ivory/60">{JOURNEY[FINALE].eyebrow}</span>
      <h2 className="mt-3 text-[40px] font-medium leading-none tracking-[-0.02em] text-ivory md:text-[clamp(52px,5.4vw,88px)]">
        {JOURNEY[FINALE].title![0]} <em className="font-display font-normal italic text-gold">{JOURNEY[FINALE].title![1]}</em>
      </h2>
      <ol className="mt-10 flex gap-5 overflow-x-auto pb-6 [perspective:1400px] [scrollbar-width:none] md:mt-14">
        {PRODUCTS.map((p, i) => {
          const room = roomOf(p.id);
          return (
            <li key={p.id} className="shrink-0" style={{ transitionDelay: `${i * 70}ms` }}>
              <button
                type="button"
                onClick={() => visit(p.id)}
                className="group/card block w-[240px] text-left transition-transform duration-700 ease-[var(--ease-cine)] [transform-style:preserve-3d] [transform:rotateY(-16deg)] hover:[transform:rotateY(0deg)_translateY(-6px)] md:w-[270px]"
              >
                <span className="block aspect-[4/5] overflow-hidden bg-charcoal">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={roomAsset(room.id, p.id, "beauty")}
                    alt={p.name}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform duration-700 group-hover/card:scale-105"
                  />
                </span>
                <span className="mt-4 flex items-baseline gap-3">
                  <span className="text-[10px] tracking-[0.18em] text-ivory/50 tabular-nums">{p.index}</span>
                  <span className="text-[15px] text-ivory">{p.name}</span>
                </span>
                <span className="mt-1 flex items-center justify-between text-[11.5px] text-ivory/55">
                  {room.name}
                  <span className="eyebrow text-gold">Discover →</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
      <p className="mt-6 text-[12px] text-ivory/45">{ROOMS.length} rooms · {PRODUCTS.length} pieces · made to order</p>
    </section>
  );
}
