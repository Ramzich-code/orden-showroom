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
