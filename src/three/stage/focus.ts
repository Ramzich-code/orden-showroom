import * as THREE from "three";
import { PRODUCT_MAP } from "@/config/products";
import { Orientation, ROOM_MAP, RoomId, SceneCamera, aspectOf, sceneCameras } from "@/config/rooms";

export interface Focus {
  /** Product centre in the frame, uv units (0..1, bottom-left origin). */
  room: THREE.Vector2;
  product: THREE.Vector2;
  /** Apparent height of the product in each still (uv), for the match cut. */
  sizeRoom: number;
  sizeProduct: number;
}

const cache = new Map<string, Focus>();

/** Where the product sits in each Blender shot (projected with the exact cameras). */
export function productFocus(room: RoomId, o: Orientation = "landscape"): Focus {
  const key = `${room}:${o}`;
  let f = cache.get(key);
  if (f) return f;
  const { scene, productId } = ROOM_MAP[room];
  const product = PRODUCT_MAP[productId];
  const point = new THREE.Vector3(...scene.product_position);
  point.y += product.hotspotY * 0.45;
  const foot = new THREE.Vector3(...scene.product_position);
  const head = foot.clone().setY(product.dimensions.height / 100);
  const camera = (c: SceneCamera) => {
    const cam = new THREE.PerspectiveCamera(c.fov, aspectOf(o), 0.05, 60);
    cam.position.set(...c.position);
    cam.quaternion.set(...c.quaternion);
    cam.updateMatrixWorld();
    return cam;
  };
  const size = (c: SceneCamera) => {
    const cam = camera(c);
    return Math.abs(head.clone().project(cam).y - foot.clone().project(cam).y) / 2;
  };
  const project = (c: SceneCamera) => {
    const p = point.clone().project(camera(c));
    return new THREE.Vector2((p.x + 1) / 2, (p.y + 1) / 2);
  };
  const cams = sceneCameras(room, o);
  f = {
    room: project(cams.room),
    product: project(cams.product),
    sizeRoom: size(cams.room),
    sizeProduct: size(cams.product),
  };
  cache.set(key, f);
  return f;
}

/** Crop rectangle (x0, y0, w, h in uv) of zoom `z` centred on `focus`, kept inside the frame. */
export function cropAround(focus: THREE.Vector2, z: number, out: THREE.Vector4) {
  const w = 1 / Math.max(1, z);
  return out.set(
    THREE.MathUtils.clamp(focus.x - w / 2, 0, 1 - w),
    THREE.MathUtils.clamp(focus.y - w / 2, 0, 1 - w),
    w,
    w,
  );
}

/**
 * Match cut between the two stills: at progress e (0..1) the product sits at
 * the same place and size in both, moving from where it is in the room still
 * to where it is in the product still. Crops may leave 0..1 (the shader then
 * shows the other still there).
 */
export function matchCrops(f: Focus, e: number, room: THREE.Vector4, product: THREE.Vector4) {
  const ratio = f.sizeProduct / f.sizeRoom;
  const x = f.room.x + (f.product.x - f.room.x) * e;
  const y = f.room.y + (f.product.y - f.room.y) * e;
  const wr = 1 / Math.pow(ratio, e);
  const wp = 1 / Math.pow(ratio, e - 1);
  room.set(f.room.x - x * wr, f.room.y - y * wr, wr, wr);
  product.set(f.product.x - x * wp, f.product.y - y * wp, wp, wp);
}
