import { FinishId, Product, formatPrice, getFinish } from "@/config/products";
import { SITE } from "@/config/site";

export const whatsappEnabled = () => SITE.whatsappNumber.length >= 8;

/** Pre-filled WhatsApp order. The number comes only from NEXT_PUBLIC_WHATSAPP_NUMBER. */
export function whatsappOrderUrl(product: Product, finish: FinishId, quantity: number): string | null {
  if (!whatsappEnabled()) return null;
  const f = getFinish(product, finish);
  const { width, depth, height } = product.dimensions;
  const lines = [
    `Hello ${SITE.brand}, I would like to order:`,
    "",
    `${product.name}`,
    `Finish: ${f.name}`,
    `Quantity: ${quantity}`,
    `Size: ${width} × ${depth} × ${height} cm`,
    product.price === null ? formatPrice(null) : `Price: ${formatPrice(product.price)} each`,
    "",
    "Name:",
    "Delivery city:",
  ];
  return `https://wa.me/${SITE.whatsappNumber}?text=${encodeURIComponent(lines.join("\n"))}`;
}
