/** Shared room dimensions (metres). Floor at y = 0, back wall at z = BACK. */
export const ROOM = {
  left: -4.6,
  right: 4.6,
  back: -3.5,
  front: 4.5,
  height: 3.0,
  window: { z0: -2.55, z1: 0.45, y0: 0.35, y1: 2.75 },
} as const;
