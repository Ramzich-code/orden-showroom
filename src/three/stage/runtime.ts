import * as THREE from "three";

/**
 * Per-frame stage values shared by the camera rig, the backdrop and the live
 * product. Mutated by gsap tweens and useFrame, never by React renders.
 */
export const runtime = {
  /** 0 = room camera, 1 = product camera. */
  shot: 0,
  /** 0 = Cycles beauty still, 1 = plate + real-time product. */
  live: 0,
  /** 0 = assembled, 1 = exploded. */
  explode: 0,
  /** Turntable angle of the live product (radians) and its drag target. */
  rotation: 0,
  rotationTarget: 0,
  /** Camera shift for the parallax, metres along the camera's right / up. */
  parallax: new THREE.Vector2(),
  /**
   * Visible part of each still (uv: x0, y0 bottom-left, w, h). Zoom crops the
   * frame; during a room <-> product move the room still pushes in towards the
   * product while the product still settles, which reads as one camera move.
   */
  cropRoom: new THREE.Vector4(0, 0, 1, 1),
  cropProduct: new THREE.Vector4(0, 0, 1, 1),
  /** Product centre in the room still (uv) and the hover spotlight amount. */
  focusRoom: new THREE.Vector2(0.5, 0.5),
  hover: 0,
};

/** Layer for the full-frame image quads, so shadow passes never see them. */
export const IMAGE_LAYER = 1;

// Dev-only handle for checking the registration of the live product.
if (process.env.NODE_ENV !== "production" && typeof window !== "undefined") {
  (window as unknown as { __ordenRuntime: typeof runtime }).__ordenRuntime = runtime;
}
