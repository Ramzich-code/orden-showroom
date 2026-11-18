"use client";

import { JOURNEY, restStep, stepStart } from "@/config/journey";
import { ROOMS, ROOM_MAP, RoomId } from "@/config/rooms";
import { scrollToVh, useJourney } from "@/lib/journey";
import { useShowroom } from "@/lib/store";

const STAGES = [
  { label: "Arrival", at: 0 },
  ...ROOMS.map((r) => ({ label: r.name, at: stepStart(restStep(r.id)) + 0.05, room: r.id as RoomId })),
  { label: "Collection", at: stepStart(JOURNEY.findIndex((s) => s.kind === "finale")) + 0.3 },
];

/**
 * Bottom bar, after the reference: where you are (room, progress, pieces), the
 * stages of the visit, and a floor plan of the house with the current room lit.
 */
export function Hud() {
  const step = useJourney((s) => s.step);
  const progress = useJourney((s) => s.progress);
  const room = useShowroom((s) => s.room);
  const visible = useShowroom((s) => s.entered && s.view === "room");
  const s = JOURNEY[step];
  const current = s.kind === "finale" ? STAGES.length - 1 : s.segment === "exterior" ? 0 : ROOMS.findIndex((r) => r.id === room) + 1;
  const r = ROOM_MAP[room];
  const light = s.segment === "exterior";
  const text = light ? "text-ivory" : "text-ink";
  const dim = light ? "text-ivory/60" : "text-charcoal/55";

  return (
    <div
      data-on={visible || undefined}
      className="pointer-events-none fixed inset-x-0 bottom-0 z-30 hidden translate-y-4 items-end justify-between gap-8 px-10 pb-7 opacity-0 transition-[opacity,transform] duration-700 ease-[var(--ease-cine)] data-on:translate-y-0 data-on:opacity-100 md:flex"
    >
      {/* where you are */}
      <dl className={`flex gap-8 text-[11px] ${text}`}>
        <div>
          <dt className={`eyebrow ${dim}`}>{current === 0 ? "Arrival" : current === STAGES.length - 1 ? "Collection" : `Room ${r.index}`}</dt>
          <dd className="mt-1 text-[15px] tabular-nums">{current === 0 ? "ORDEN House" : current === STAGES.length - 1 ? "6 pieces" : r.name}</dd>
        </div>
        <div>
          <dt className={`eyebrow ${dim}`}>Visit</dt>
          <dd className="mt-1 text-[15px] tabular-nums">{String(Math.round(progress * 100)).padStart(2, "0")}%</dd>
        </div>
        {current > 0 && current < STAGES.length - 1 && (
          <div>
            <dt className={`eyebrow ${dim}`}>Pieces</dt>
            <dd className="mt-1 text-[15px] tabular-nums">{r.productIds.length}</dd>
          </div>
        )}
      </dl>

      {/* stages */}
      <ol className="pointer-events-auto flex items-end gap-6">
        {STAGES.map((st, i) => (
          <li key={st.label}>
            <button
              type="button"
              onClick={() => scrollToVh(st.at)}
              data-on={i === current || undefined}
              className={`flex flex-col items-center gap-2 text-[10.5px] tracking-[0.14em] uppercase transition-colors ${i === current ? text : dim}`}
            >
              <span className={`h-px w-10 transition-colors ${i <= current ? "bg-gold" : light ? "bg-ivory/30" : "bg-charcoal/20"}`} />
              <span>{st.label}</span>
            </button>
          </li>
        ))}
      </ol>

      {/* floor plan */}
      <FloorPlan current={current} light={light} />
    </div>
  );
}

function FloorPlan({ current, light }: { current: number; light: boolean }) {
  const stroke = light ? "rgb(244 240 232 / 0.7)" : "rgb(35 33 31 / 0.45)";
  const rooms = [
    { x: 2, y: 2, w: 52, h: 46, label: "01" },
    { x: 54, y: 2, w: 38, h: 46, label: "02" },
    { x: 92, y: 2, w: 40, h: 46, label: "03" },
  ];
  return (
    <svg width="150" height="62" viewBox="0 0 134 62" aria-label="Floor plan" className="shrink-0">
      {rooms.map((rm, i) => (
        <g key={rm.label}>
          <rect
            x={rm.x}
            y={rm.y}
            width={rm.w}
            height={rm.h}
            fill={current === i + 1 ? "rgb(176 138 82 / 0.35)" : "transparent"}
            stroke={current === i + 1 ? "#b08a52" : stroke}
            strokeWidth="1"
          />
          <text x={rm.x + 5} y={rm.y + 12} fontSize="8" fill={current === i + 1 ? "#b08a52" : stroke} letterSpacing="1">
            {rm.label}
          </text>
        </g>
      ))}
      <line x1="40" y1="48" x2="40" y2="60" stroke={current === 0 ? "#b08a52" : stroke} />
      <text x="46" y="59" fontSize="7" fill={stroke} letterSpacing="1">
        ENTRANCE
      </text>
    </svg>
  );
}
