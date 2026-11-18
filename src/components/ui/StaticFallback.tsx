import { PRODUCT_MAP, finishesOf, formatPrice, getFinish } from "@/config/products";
import { ROOMS, roomAsset } from "@/config/rooms";
import { SITE } from "@/config/site";
import { whatsappOrderUrl } from "@/lib/whatsapp";

/**
 * Shown when WebGL is unavailable: the same three rooms as Cycles stills,
 * the same catalogue and the same WhatsApp ordering, without the live 3D.
 */
export function StaticFallback() {
  return (
    <main className="min-h-full bg-ivory px-5 py-8 md:px-10 md:py-12">
      <header className="flex flex-col gap-1.5">
        <span className="text-[13px] font-semibold tracking-[0.5em]">{SITE.brand}</span>
        <span className="eyebrow text-stone">{SITE.descriptor}</span>
      </header>
      <h1 className="mt-14 font-display text-[52px] leading-[0.95] text-ink md:text-[88px]">
        Designed to <em>belong.</em>
      </h1>
      <ol className="mt-12 flex flex-col gap-16">
        {ROOMS.map((room) => {
          return (
            <li key={room.id}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={roomAsset(room.id, "room", "beauty")} alt={room.title} className="aspect-video w-full object-cover" loading="lazy" />
              {room.productIds.map((id) => {
                const p = PRODUCT_MAP[id];
                const order = whatsappOrderUrl(p, p.defaultFinish, 1);
                return (
              <div key={id} className="mt-6 grid gap-3 md:grid-cols-[80px_1fr_1fr] md:gap-8">
                <span className="text-[11px] tracking-[0.18em] text-stone">{p.index}</span>
                <div>
                  <h2 className="font-display text-[32px] leading-none text-ink">{p.name}</h2>
                  <p className="mt-2 text-[13px] text-charcoal/70">{p.tagline}</p>
                </div>
                <div className="text-[13px] leading-relaxed text-charcoal/75">
                  <p>{p.description}</p>
                  <p className="mt-3 text-charcoal/60">
                    {p.dimensions.width} × {p.dimensions.depth} × {p.dimensions.height} cm ·{" "}
                    {finishesOf(p).map((f) => getFinish(p, f).name).join(" / ")} · {formatPrice(p.price)}
                  </p>
                  {order && (
                    <a href={order} target="_blank" rel="noopener noreferrer" className="mt-4 inline-block bg-ink px-5 py-3 text-[12.5px] text-paper">
                      Order on WhatsApp
                    </a>
                  )}
                </div>
              </div>
                );
              })}
            </li>
          );
        })}
      </ol>
    </main>
  );
}
