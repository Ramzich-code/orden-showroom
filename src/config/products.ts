/**
 * ORDEN: product catalogue (Collection 001).
 *
 * 3D MODELS
 * ---------
 * public/models/<id>.glb is exported from the approved Blender geometry
 * (blender/products/export_glb.py). Each component is a node named like
 * `components[].id` below and carries its material role as glTF extras
 * (`role`), so finishes and the exploded view need no code changes when a
 * model is replaced, as long as the names and roles are kept.
 */
import { asset } from "@/config/site";

export type Vec3 = [number, number, number];

export type FinishId = "signature" | "white" | "black" | "oak";

/** How a component reacts to a finish change (see src/three/materials.ts). */
export type MaterialRole =
  | "body"
  | "accent"
  | "travertine"
  | "marble"
  | "base"
  | "metal"
  | "interior"
  | "fabric" // fixed oatmeal boucle (sofa, bench cushion)
  | "socket" // fixed anthracite socket plates
  | "light"; // LED diffusers (emissive)

export interface Finish {
  id: FinishId;
  name: string;
  swatch: string;
  description: string;
}

export const FINISHES: Record<Exclude<FinishId, "signature">, Finish> = {
  white: { id: "white", name: "White", swatch: "#EDEAE5", description: "Matte lacquer, soft mineral white" },
  black: { id: "black", name: "Black", swatch: "#252321", description: "Deep matte lacquer" },
  oak: { id: "oak", name: "Natural Oak", swatch: "#B98A57", description: "Oak veneer, oiled" },
};

export const FINISH_ORDER: FinishId[] = ["signature", "white", "black", "oak"];

export interface ProductComponent {
  /** Node name in the GLB. */
  id: string;
  label: string;
  detail?: string;
  /** Offset (product-local metres, Y-up, +Z = front) at full explosion. */
  explode: Vec3;
  /** Show a label for this component in the exploded view. */
  annotate?: boolean;
}

export type ProductId = "coffee-table" | "bedside-table" | "wardrobe" | "sofa" | "headboard-shelf" | "shoe-bench";

export interface Product {
  id: ProductId;
  index: string;
  name: string;
  line: string;
  tagline: string;
  description: string;
  /** Price in EUR. null renders "Price on request". */
  price: number | null;
  dimensions: { width: number; depth: number; height: number }; // centimetres
  details: string[];
  /** The reference look, offered as the first finish. */
  signature: { name: string; swatch: string; description: string; body: "walnut" | "taupe" | "greige" | "oak" };
  defaultFinish: FinishId;
  /** Finishes offered (default: all of FINISH_ORDER). */
  finishes?: FinishId[];
  model: string;
  components: ProductComponent[];
  /** Height (m) of the hotspot pin above the product origin. */
  hotspotY: number;
}

export const finishesOf = (product: Product): FinishId[] => product.finishes ?? FINISH_ORDER;

export function getFinish(product: Product, id: FinishId): Finish {
  if (id === "signature") return { id, ...product.signature };
  return FINISHES[id];
}

export const PRODUCTS: Product[] = [
  {
    id: "coffee-table",
    index: "01",
    name: "Lune Coffee Table",
    line: "Living",
    tagline: "Two identical slabs, one quiet offset.",
    description:
      "Two softly rounded slabs of the same size, travertine over solid wood, held apart by a single dark panel at one end. The open gap between them carries books, the stone carries the rest.",
    price: null,
    dimensions: { width: 113, depth: 102, height: 29 },
    details: ["Honed travertine top · 70 mm", "Solid wood lower slab · 70 mm", "Side panel · 30 mm", "Open shelf between the slabs"],
    signature: {
      name: "Travertine & Walnut",
      swatch: "#4A3122",
      description: "Honed travertine top, oiled walnut",
      body: "walnut",
    },
    defaultFinish: "signature",
    model: asset("/models/coffee-table.glb"),
    components: [
      { id: "top", label: "Top slab", detail: "Travertine · 70 mm", explode: [0, 0.32, 0], annotate: true },
      { id: "panel", label: "Side panel", detail: "Solid · 30 mm", explode: [-0.32, 0.08, 0], annotate: true },
      { id: "platform", label: "Lower slab", detail: "Same footprint as the top", explode: [0, 0, 0], annotate: true },
    ],
    hotspotY: 0.5,
  },
  {
    id: "bedside-table",
    index: "02",
    name: "Hvile Bedside Table",
    line: "Bedroom",
    tagline: "Close at hand, quiet by nature.",
    description:
      "A low cabinet whose sides and back rise just above a marble-effect top, framing it like a tray. An open shelf for books, a deep handleless drawer, and a dark recessed base that lets it hover.",
    price: null,
    dimensions: { width: 60, depth: 55, height: 50 },
    details: ["Marble-effect top set in a raised frame", "Open shelf", "Full-width handleless drawer", "Recessed plinth"],
    signature: {
      name: "Taupe & Marble",
      swatch: "#A99A7C",
      description: "Matte taupe lacquer, white marble-effect top",
      body: "taupe",
    },
    defaultFinish: "signature",
    model: asset("/models/bedside-table.glb"),
    components: [
      { id: "top", label: "Top", detail: "Marble-effect · 30 mm", explode: [0, 0.3, 0.04], annotate: true },
      { id: "side-l", label: "Side", detail: "Raised 20 mm frame", explode: [-0.26, 0.02, 0], annotate: true },
      { id: "side-r", label: "Side", explode: [0.26, 0.02, 0] },
      { id: "back", label: "Back panel", explode: [0, 0.02, -0.28], annotate: true },
      { id: "shelf", label: "Shelf", detail: "Open niche", explode: [0, 0.14, 0.1] },
      { id: "drawer-front", label: "Drawer front", detail: "Handleless", explode: [0, -0.02, 0.42], annotate: true },
      { id: "drawer-box", label: "Drawer box", explode: [0, -0.02, 0.24] },
      { id: "bottom", label: "Bottom", explode: [0, 0.03, 0.06] },
      { id: "plinth", label: "Plinth", detail: "Recessed", explode: [0, -0.04, 0], annotate: true },
    ],
    hotspotY: 0.72,
  },
  {
    id: "wardrobe",
    index: "03",
    name: "Fjell Wardrobe",
    line: "Dressing",
    tagline: "Architecture for what you keep.",
    description:
      "A tall, calm volume with softly rounded edges and two flush doors set between the sides. Inside, a full-width shelf and hanging rail. Raised on short legs so light runs underneath.",
    price: null,
    dimensions: { width: 108, depth: 58, height: 201 },
    details: ["Two flush doors between rounded sides", "Full-width shelf and steel rail", "Slim 35 cm pulls", "Raised on 6 cm legs"],
    signature: { name: "Warm Greige", swatch: "#D6C9B5", description: "Matte lacquer, warm greige, walnut pulls", body: "greige" },
    defaultFinish: "signature",
    model: asset("/models/wardrobe.glb"),
    components: [
      { id: "door-l", label: "Door", detail: "22 mm · flush", explode: [-0.28, 0, 0.75], annotate: true },
      { id: "door-r", label: "Door", explode: [0.28, 0, 0.75] },
      { id: "handle-l", label: "Pull", detail: "350 mm", explode: [-0.28, 0, 1.0], annotate: true },
      { id: "handle-r", label: "Pull", explode: [0.28, 0, 1.0] },
      { id: "side-l", label: "Side", detail: "Rounded edge", explode: [-0.5, 0, 0], annotate: true },
      { id: "side-r", label: "Side", explode: [0.5, 0, 0] },
      { id: "top", label: "Top", explode: [0, 0.4, 0] },
      { id: "base", label: "Base", explode: [0, -0.04, 0.3] },
      { id: "back", label: "Back panel", explode: [0, 0, -0.45], annotate: true },
      { id: "shelf", label: "Shelf", explode: [0, 0.1, 0.45], annotate: true },
      { id: "rail", label: "Hanging rail", detail: "Brushed steel", explode: [0, 0.05, 0.6], annotate: true },
      { id: "leg-fl", label: "Leg", detail: "60 mm", explode: [-0.12, -0.08, 0.12], annotate: true },
      { id: "leg-fr", label: "Leg", explode: [0.12, -0.08, 0.12] },
      { id: "leg-bl", label: "Leg", explode: [-0.12, -0.08, -0.12] },
      { id: "leg-br", label: "Leg", explode: [0.12, -0.08, -0.12] },
    ],
    hotspotY: 2.2,
  },
  {
    id: "sofa",
    index: "04",
    name: "Mjuk Sofa",
    line: "Living",
    tagline: "Soft all the way round.",
    description:
      "A long, low three-seater in oatmeal boucle where every volume is a cushion: rolled arms that lean back into the frame, two deep seats whose front runs almost to the floor and two generous back cushions.",
    price: null,
    dimensions: { width: 260, depth: 100, height: 76 },
    details: ["Oatmeal boucle, removable covers", "Rolled arms, feather-wrapped foam", "Two seat and two back cushions", "Hidden recessed base"],
    signature: { name: "Oat Bouclé", swatch: "#D8CCB8", description: "Wool-blend boucle, oatmeal", body: "oak" },
    defaultFinish: "signature",
    finishes: ["signature"],
    model: asset("/models/sofa.glb"),
    components: [
      { id: "back-cushion-l", label: "Back cushion", detail: "Feather & foam", explode: [-0.05, 0.3, -0.05], annotate: true },
      { id: "back-cushion-r", label: "Back cushion", explode: [0.05, 0.3, -0.05] },
      { id: "seat-l", label: "Seat cushion", detail: "High-resilience foam", explode: [-0.06, 0.2, 0.35], annotate: true },
      { id: "seat-r", label: "Seat cushion", explode: [0.06, 0.2, 0.35] },
      { id: "arm-l", label: "Arm", detail: "Rolled", explode: [-0.4, 0, 0], annotate: true },
      { id: "arm-r", label: "Arm", explode: [0.4, 0, 0] },
      { id: "back", label: "Frame", detail: "Solid beech", explode: [0, 0.05, -0.35], annotate: true },
      { id: "base", label: "Base", explode: [0, -0.02, 0] },
    ],
    hotspotY: 0.95,
  },
  {
    id: "headboard-shelf",
    index: "05",
    name: "Lys Headboard Shelf",
    line: "Bedroom",
    tagline: "Light and power, right behind you.",
    description:
      "An oak ledge along the top of the bed head. Two LED strips set into it wash the wall with warm light; a row of four sockets and a socket with USB charge everything you keep at night, with no cable on the floor.",
    price: null,
    dimensions: { width: 220, depth: 16, height: 15 },
    details: ["Solid oak, 25 mm", "Two warm LED strips (2700 K)", "Four sockets + one with USB", "Wall-mounted on a hidden apron"],
    signature: { name: "Natural Oak", swatch: "#C8A77C", description: "Oak, oiled, anthracite sockets", body: "oak" },
    defaultFinish: "signature",
    finishes: ["signature", "white", "black"],
    model: asset("/models/headboard-shelf.glb"),
    components: [
      { id: "shelf", label: "Ledge", detail: "Oak · 25 mm", explode: [0, 0.16, 0], annotate: true },
      { id: "led-l", label: "LED strip", detail: "2700 K, opal diffuser", explode: [0, 0.3, 0], annotate: true },
      { id: "led-r", label: "LED strip", explode: [0, 0.3, 0] },
      { id: "sockets", label: "Sockets", detail: "4 × flush", explode: [0, 0.28, 0.06], annotate: true },
      { id: "usb-socket", label: "Socket + USB", explode: [0, 0.28, 0.06] },
      { id: "socket-end", label: "Socket", explode: [0, 0.28, 0.06] },
      { id: "apron", label: "Wall apron", detail: "Hidden", explode: [0, -0.12, -0.04], annotate: true },
      { id: "bracket-l", label: "Bracket", explode: [0, -0.04, 0] },
      { id: "bracket-r", label: "Bracket", explode: [0, -0.04, 0] },
    ],
    hotspotY: 1.38,
  },
  {
    id: "shoe-bench",
    index: "06",
    name: "Sko Shoe Bench",
    line: "Dressing",
    tagline: "Sit down, put them on.",
    description:
      "A low oak bench to sit on while you dress: a boucle cushion over three open bays with a shelf for shoes, and the collection's dark recessed plinth.",
    price: null,
    dimensions: { width: 120, depth: 38, height: 47 },
    details: ["Oak, 22 mm", "Boucle cushion, removable cover", "Three bays, six shoe compartments", "Recessed plinth"],
    signature: { name: "Natural Oak", swatch: "#C8A77C", description: "Oak, oiled, oatmeal boucle cushion", body: "oak" },
    defaultFinish: "signature",
    finishes: ["signature", "white", "black"],
    model: asset("/models/shoe-bench.glb"),
    components: [
      { id: "cushion", label: "Cushion", detail: "Boucle · 60 mm", explode: [0, 0.32, 0], annotate: true },
      { id: "top", label: "Top", explode: [0, 0.2, 0] },
      { id: "side-l", label: "Side", detail: "Oak · 22 mm", explode: [-0.28, 0, 0], annotate: true },
      { id: "side-r", label: "Side", explode: [0.28, 0, 0] },
      { id: "divider-l", label: "Divider", explode: [-0.1, 0, 0.2] },
      { id: "divider-r", label: "Divider", explode: [0.1, 0, 0.2] },
      { id: "shelf", label: "Shoe shelf", explode: [0, 0.04, 0.3], annotate: true },
      { id: "bottom", label: "Bottom", explode: [0, -0.02, 0.12] },
      { id: "back", label: "Back", explode: [0, 0, -0.25] },
      { id: "plinth", label: "Plinth", detail: "Recessed", explode: [0, -0.05, 0], annotate: true },
    ],
    hotspotY: 0.72,
  },
];

export const PRODUCT_MAP = Object.fromEntries(PRODUCTS.map((p) => [p.id, p])) as Record<ProductId, Product>;

export function formatPrice(price: number | null): string {
  if (price === null) return "Price on request";
  return new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(price);
}
