export const SITE = {
  brand: "ORDEN",
  descriptor: "Furniture & Objects",
  tagline: "Designed to belong.",
  room: "Living Room No. 01",
  /**
   * Order destination. Set NEXT_PUBLIC_WHATSAPP_NUMBER in `.env.local`
   * (international format, digits only). Left empty on purpose: no number is
   * hard-coded in the source.
   */
  whatsappNumber: (process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "").replace(/\D/g, ""),
} as const;

/** Sub-path the site is served under (GitHub Pages: "/orden-showroom"); empty locally. */
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
/** Public file URL ("/models/x.glb") with the base path in front. */
export const asset = (path: string) => `${BASE_PATH}${path}`;
