"use client";

import { create } from "zustand";
import { FinishId, PRODUCTS, ProductId } from "@/config/products";
import { ROOMS, ROOM_MAP, RoomId } from "@/config/rooms";

/** room = establishing view of the room; product = the product shot (live 3D). */
export type View = "room" | "product";
export type Quality = "high" | "low";

interface ShowroomState {
  /** The stage has its first room's images and model ready. */
  sceneReady: boolean;
  /** Loader has faded out. */
  entered: boolean;
  quality: Quality;
  /** prefers-reduced-motion: short dissolves, no parallax or push-ins. */
  reducedMotion: boolean;
  room: RoomId;
  view: View;
  /** True while the stage fades between two rooms. */
  switching: boolean;
  /** The product in focus in this room (its camera is the product view). */
  selected: ProductId;
  hovered: ProductId | null;
  exploded: boolean;
  /** Zoom factor in the product view (1 = framing of the still). */
  zoom: number;
  finishes: Record<ProductId, FinishId>;
  quantities: Record<ProductId, number>;
  orderOpen: boolean;

  setSceneReady: (ready: boolean) => void;
  enter: () => void;
  setQuality: (q: Quality) => void;
  setReducedMotion: (r: boolean) => void;
  nextRoom: (dir: 1 | -1) => void;
  goToRoom: (room: RoomId) => void;
  /** Room change hidden behind the journey frames: no dissolve. */
  enterRoomCovered: (room: RoomId) => void;
  finishSwitch: () => void;
  /** Opens a product of the current room (default: the selected one). */
  openProduct: (id?: ProductId) => void;
  /** From the product view, go to another product of the room (via the room view). */
  visitProduct: (id: ProductId) => void;
  backToRoom: () => void;
  setHovered: (id: ProductId | null) => void;
  setFinish: (id: ProductId, finish: FinishId) => void;
  setQuantity: (id: ProductId, q: number) => void;
  toggleExploded: () => void;
  setZoom: (z: number) => void;
  setOrderOpen: (open: boolean) => void;
}

export const ZOOM_RANGE: [number, number] = [1, 2.4];

const byProduct = <T,>(f: (id: ProductId) => T) =>
  Object.fromEntries(PRODUCTS.map((p) => [p.id, f(p.id)])) as Record<ProductId, T>;

export const useShowroom = create<ShowroomState>((set, get) => ({
  sceneReady: false,
  entered: false,
  quality: "high",
  reducedMotion: false,
  room: "living",
  view: "room",
  switching: false,
  selected: ROOM_MAP.living.productIds[0],
  hovered: null,
  exploded: false,
  zoom: 1,
  finishes: byProduct((id) => PRODUCTS.find((p) => p.id === id)!.defaultFinish),
  quantities: byProduct(() => 1),
  orderOpen: false,

  setSceneReady: (sceneReady) => set({ sceneReady }),
  enter: () => set({ entered: true }),
  setQuality: (quality) => set({ quality }),
  setReducedMotion: (reducedMotion) => set({ reducedMotion }),
  nextRoom: (dir) => {
    const ids = ROOMS.map((r) => r.id);
    get().goToRoom(ids[(ids.indexOf(get().room) + dir + ids.length) % ids.length]);
  },
  goToRoom: (room) => {
    if (room === get().room && !get().switching) return;
    set({ room, switching: true, view: "room", exploded: false, zoom: 1, hovered: null, orderOpen: false, selected: ROOM_MAP[room].productIds[0] });
  },
  enterRoomCovered: (room) => {
    if (room === get().room) return;
    set({ room, switching: false, view: "room", exploded: false, zoom: 1, hovered: null, orderOpen: false, selected: ROOM_MAP[room].productIds[0] });
  },
  finishSwitch: () => set({ switching: false }),
  openProduct: (id) => set((s) => ({ view: "product", hovered: null, selected: id ?? s.selected })),
  visitProduct: (id) => {
    if (get().view === "room") return get().openProduct(id);
    get().backToRoom();
    setTimeout(() => {
      if (get().view === "room" && ROOM_MAP[get().room].productIds.includes(id)) get().openProduct(id);
    }, 2600);
  },
  backToRoom: () => set({ view: "room", exploded: false, zoom: 1, orderOpen: false }),
  setHovered: (hovered) => set({ hovered }),
  setFinish: (id, finish) => set((s) => ({ finishes: { ...s.finishes, [id]: finish } })),
  setQuantity: (id, q) => set((s) => ({ quantities: { ...s.quantities, [id]: Math.max(1, Math.min(20, Math.round(q))) } })),
  toggleExploded: () => set((s) => ({ exploded: !s.exploded, zoom: 1 })),
  setZoom: (z) => set({ zoom: Math.max(ZOOM_RANGE[0], Math.min(ZOOM_RANGE[1], z)) }),
  setOrderOpen: (orderOpen) => set({ orderOpen }),
}));


// Dev-only handle for inspecting/driving state from the browser console.
if (process.env.NODE_ENV !== "production" && typeof window !== "undefined") {
  (window as unknown as { __orden: typeof useShowroom }).__orden = useShowroom;
}
