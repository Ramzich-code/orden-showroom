"use client";

import { PRODUCT_MAP, finishesOf, formatPrice, getFinish } from "@/config/products";
import { ROOM_MAP } from "@/config/rooms";
import { useShowroom, ZOOM_RANGE } from "@/lib/store";
import { whatsappEnabled, whatsappOrderUrl } from "@/lib/whatsapp";

/**
 * Product view: details, finishes, quantity, WhatsApp order, and the
 * inspection tools (explode, zoom). Right panel on desktop (420 px, matches
 * PANEL_W in Stage), bottom sheet on mobile.
 */
export function ProductPanel() {
  const productId = useShowroom((s) => s.selected);
  const room = useShowroom((s) => s.room);
  const others = ROOM_MAP[room].productIds.filter((id) => id !== productId);
  const open = useShowroom((s) => s.view === "product" && !s.switching);
  const finish = useShowroom((s) => s.finishes[productId]);
  const quantity = useShowroom((s) => s.quantities[productId]);
  const exploded = useShowroom((s) => s.exploded);
  const zoom = useShowroom((s) => s.zoom);
  const { setFinish, setQuantity, toggleExploded, setZoom, backToRoom, visitProduct } = useShowroom.getState();
  const product = PRODUCT_MAP[productId];
  const current = getFinish(product, finish);
  const orderUrl = whatsappOrderUrl(product, finish, quantity);
  const { width, depth, height } = product.dimensions;

  return (
    <>
      {/* inspection tools, over the stage */}
      <div
        data-on={open || undefined}
        className="pointer-events-none absolute left-5 top-24 z-20 flex flex-col items-start gap-3 opacity-0 transition-opacity delay-300 duration-700 data-on:pointer-events-auto data-on:opacity-100 md:left-10 md:top-auto md:bottom-12"
      >
        <button type="button" onClick={backToRoom} className="eyebrow flex items-center gap-2 bg-paper/80 px-3 py-2 text-ink backdrop-blur-md">
          <svg width="18" height="10" viewBox="0 0 18 10" fill="none" aria-hidden>
            <path d="M18 5H2M6 1 2 5l4 4" stroke="currentColor" strokeWidth="1" />
          </svg>
          Back to the room
        </button>
        <div className="flex items-center gap-1 bg-paper/80 p-1 backdrop-blur-md">
          <button type="button" onClick={toggleExploded} aria-pressed={exploded} className="tool">
            {exploded ? "Reassemble" : "Explode"}
          </button>
          <span className="mx-1 h-5 w-px bg-charcoal/15" />
          <button type="button" onClick={() => setZoom(zoom / 1.35)} disabled={zoom <= ZOOM_RANGE[0]} className="tool w-9" aria-label="Zoom out">
            −
          </button>
          <button type="button" onClick={() => setZoom(zoom * 1.35)} disabled={zoom >= ZOOM_RANGE[1]} className="tool w-9" aria-label="Zoom in">
            +
          </button>
        </div>
        <span className="hidden text-[11.5px] tracking-[0.04em] text-charcoal/70 md:block">Drag to turn · Scroll to zoom</span>
      </div>

      <aside
        data-on={open || undefined}
        aria-label={product.name}
        aria-hidden={!open}
        className="absolute inset-x-0 bottom-0 z-30 max-h-[45vh] translate-y-full overflow-y-auto bg-paper px-5 pb-6 pt-5 shadow-[0_-12px_40px_rgb(35_33_31/0.08)] transition-transform duration-[900ms] ease-[var(--ease-cine)] data-on:translate-y-0 md:inset-y-0 md:left-auto md:right-0 md:max-h-none md:w-[420px] md:translate-x-full md:translate-y-0 md:px-10 md:pb-10 md:pt-28 md:shadow-[-12px_0_40px_rgb(35_33_31/0.06)] md:data-on:translate-x-0"
      >
        <span className="eyebrow text-stone">
          {product.index} · {product.line}
        </span>
        <h2 className="mt-2 font-display text-[38px] leading-[0.95] text-ink md:mt-3 md:text-[46px]">{product.name}</h2>
        <p className="mt-2 text-[13.5px] text-charcoal/70">{product.tagline}</p>

        <div className="mt-6 border-t border-charcoal/12 pt-5">
          <div className="flex items-baseline justify-between">
            <span className="eyebrow text-charcoal/70">Finish</span>
            <span className="text-[12.5px] text-ink">{current.name}</span>
          </div>
          <div className="mt-3 flex gap-2.5" role="radiogroup" aria-label="Finish">
            {finishesOf(product).map((id) => {
              const f = getFinish(product, id);
              return (
                <button
                  key={id}
                  type="button"
                  role="radio"
                  aria-checked={finish === id}
                  aria-label={f.name}
                  title={f.name}
                  onClick={() => setFinish(product.id, id)}
                  className="h-9 w-9 rounded-full p-[3px] ring-1 ring-charcoal/15 transition-shadow duration-300 aria-checked:ring-ink"
                >
                  <span className="block h-full w-full rounded-full" style={{ background: f.swatch }} />
                </button>
              );
            })}
          </div>
          <p className="mt-2.5 text-[12px] text-charcoal/60">{current.description}</p>
        </div>

        <p className="mt-6 text-[13.5px] leading-relaxed text-charcoal/80">{product.description}</p>
        <dl className="mt-5 grid grid-cols-3 border-y border-charcoal/12 py-3 text-[12px]">
          {[
            ["Width", width],
            ["Depth", depth],
            ["Height", height],
          ].map(([k, v]) => (
            <div key={k}>
              <dt className="text-charcoal/55">{k}</dt>
              <dd className="mt-0.5 text-ink tabular-nums">{v} cm</dd>
            </div>
          ))}
        </dl>
        <ul className="mt-4 flex flex-col gap-1.5 text-[12.5px] text-charcoal/70">
          {product.details.map((d) => (
            <li key={d} className="flex gap-2">
              <span className="mt-[7px] h-px w-3 bg-charcoal/30" aria-hidden />
              {d}
            </li>
          ))}
        </ul>

        <div className="mt-7 flex items-center justify-between">
          <span className="text-[15px] text-ink">{formatPrice(product.price)}</span>
          <div className="flex items-center border border-charcoal/15" role="group" aria-label="Quantity">
            <button type="button" className="h-9 w-9 text-ink disabled:text-charcoal/30" onClick={() => setQuantity(product.id, quantity - 1)} disabled={quantity <= 1} aria-label="Decrease quantity">
              −
            </button>
            <span className="w-8 text-center text-[13px] tabular-nums" aria-live="polite">
              {quantity}
            </span>
            <button type="button" className="h-9 w-9 text-ink" onClick={() => setQuantity(product.id, quantity + 1)} aria-label="Increase quantity">
              +
            </button>
          </div>
        </div>

        {orderUrl ? (
          <a
            href={orderUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 flex h-12 w-full items-center justify-center gap-3 bg-ink text-[13px] tracking-[0.04em] text-paper transition-colors duration-300 hover:bg-charcoal"
          >
            <WhatsAppIcon />
            Order on WhatsApp
          </a>
        ) : (
          <div className="mt-4">
            <button type="button" disabled className="flex h-12 w-full items-center justify-center gap-3 bg-charcoal/25 text-[13px] text-paper">
              <WhatsAppIcon />
              Order on WhatsApp
            </button>
            {!whatsappEnabled() && (
              <p className="mt-2 text-[11.5px] text-charcoal/60">Ordering opens once the WhatsApp number is configured.</p>
            )}
          </div>
        )}

        {others.length > 0 && (
          <div className="mt-8 border-t border-charcoal/12 pt-5">
            <span className="eyebrow text-charcoal/70">Also in this room</span>
            <ul className="mt-3 flex flex-col">
              {others.map((id) => (
                <li key={id}>
                  <button
                    type="button"
                    onClick={() => visitProduct(id)}
                    className="group/other flex w-full items-baseline gap-3 border-b border-charcoal/10 py-3 text-left"
                  >
                    <span className="text-[10px] tracking-[0.18em] text-stone tabular-nums">{PRODUCT_MAP[id].index}</span>
                    <span className="flex-1 text-[13.5px] text-ink transition-transform duration-500 group-hover/other:translate-x-1">
                      {PRODUCT_MAP[id].name}
                    </span>
                    <span aria-hidden className="text-charcoal/50">→</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </>
  );
}

function WhatsAppIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.2 2.2 2.2 0 0 0 .1-1.2c0-.2-.2-.2-.4-.3Z" />
    </svg>
  );
}
