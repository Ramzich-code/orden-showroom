"use client";

import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { useTexture } from "@react-three/drei";
import { Orientation, ROOM_MAP, RoomId, aspectOf, roomAsset, sceneCameras } from "@/config/rooms";
import { IMAGE_LAYER, runtime } from "./runtime";

const VERT = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

/*
 * Draws the Cycles stills with a depth-based parallax that matches the real
 * camera shift: a point at distance z moves by f * shift / z on screen, so the
 * still and the live GLB (rendered with the shifted camera) stay registered.
 */
const FRAG = /* glsl */ `
  uniform sampler2D uImgRoom, uImgProduct, uDepthRoom, uDepthProduct;
  uniform vec2 uFocalRoom, uFocalProduct;   // 1 / (2 tan(fov/2)), x and y
  uniform vec2 uDepthRange;                  // near, far (m)
  uniform vec2 uShift;                       // camera shift, m (right, up)
  uniform vec4 uCropRoom, uCropProduct;
  uniform vec2 uFocus;                       // product in the room still (uv)
  uniform float uShot, uOpacity, uHover, uAspect;
  varying vec2 vUv;

  vec3 shot(sampler2D img, sampler2D depth, vec2 focal, vec2 uv) {
    float d = texture2D(depth, uv).r;                       // white = near
    float z = uDepthRange.x + (1.0 - d) * (uDepthRange.y - uDepthRange.x);
    vec2 src = clamp(uv + uShift * focal / max(z, 0.4), vec2(0.0), vec2(1.0));
    return texture2D(img, src).rgb;
  }

  void main() {
    vec2 uvA = uCropRoom.xy + vUv * uCropRoom.zw;
    vec2 uvB = uCropProduct.xy + vUv * uCropProduct.zw;
    vec3 a = uShot < 0.999 ? shot(uImgRoom, uDepthRoom, uFocalRoom, uvA) : vec3(0.0);
    vec3 b = uShot > 0.001 ? shot(uImgProduct, uDepthProduct, uFocalProduct, uvB) : vec3(0.0);
    // dissolve in the middle of the move; where a still has no pixels (crop
    // outside the image) the other one fills in
    vec2 ea = min(uvA, 1.0 - uvA), eb = min(uvB, 1.0 - uvB);
    float inA = smoothstep(-0.002, 0.02, min(ea.x, ea.y));
    float inB = smoothstep(-0.002, 0.02, min(eb.x, eb.y));
    float m = smoothstep(0.3, 0.75, uShot);
    float wa = (1.0 - m) * inA + 1e-4 * step(m, 0.5);
    float wb = m * inB + 1e-4 * step(0.5, m);
    // hover: the room settles back a touch around the product (soft spotlight)
    vec2 d = (uvA - uFocus) * vec2(uAspect, 1.0);
    float spot = 1.0 - smoothstep(0.12, 0.55, length(d));
    a *= mix(1.0, 0.9 + 0.1 * spot, uHover);
    gl_FragColor = vec4((a * wa + b * wb) / (wa + wb), uOpacity);
    #include <colorspace_fragment>
  }
`;

function focal(fovDeg: number, aspect: number) {
  const tv = Math.tan(THREE.MathUtils.degToRad(fovDeg) / 2);
  return new THREE.Vector2(1 / (2 * tv * aspect), 1 / (2 * tv));
}

/**
 * kind "plate": drawn first, behind everything (the room without the product).
 * kind "beauty": drawn last, over the live product, faded out as it goes live.
 */
export function Backdrop({ room, kind, orient }: { room: RoomId; kind: "plate" | "beauty"; orient: Orientation }) {
  const { scene } = ROOM_MAP[room];
  const cams = sceneCameras(room, orient);
  const aspect = aspectOf(orient);
  const [imgRoom, imgProduct, depthRoom, depthProduct] = useTexture([
    roomAsset(room, "room", kind, orient),
    roomAsset(room, "product", kind, orient),
    roomAsset(room, "room", "depth", orient),
    roomAsset(room, "product", "depth", orient),
  ]);

  useLayoutEffect(() => {
    for (const t of [imgRoom, imgProduct]) {
      t.colorSpace = THREE.SRGBColorSpace;
      t.needsUpdate = true;
    }
    for (const t of [depthRoom, depthProduct]) {
      t.colorSpace = THREE.NoColorSpace;
      t.needsUpdate = true;
    }
  }, [imgRoom, imgProduct, depthRoom, depthProduct]);

  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: VERT,
        fragmentShader: FRAG,
        uniforms: {
          uImgRoom: { value: imgRoom },
          uImgProduct: { value: imgProduct },
          uDepthRoom: { value: depthRoom },
          uDepthProduct: { value: depthProduct },
          uFocalRoom: { value: focal(cams.room.fov, aspect) },
          uFocalProduct: { value: focal(cams.product.fov, aspect) },
          uAspect: { value: aspect },
          uDepthRange: { value: new THREE.Vector2(scene.depth.near, scene.depth.far) },
          uShift: { value: new THREE.Vector2() },
          uCropRoom: { value: new THREE.Vector4(0, 0, 1, 1) },
          uCropProduct: { value: new THREE.Vector4(0, 0, 1, 1) },
          uFocus: { value: new THREE.Vector2(0.5, 0.5) },
          uHover: { value: 0 },
          uShot: { value: 0 },
          uOpacity: { value: 1 },
        },
        depthTest: false,
        depthWrite: false,
        transparent: kind === "beauty",
        toneMapped: false,
      }),
    [imgRoom, imgProduct, depthRoom, depthProduct, scene, kind, cams, aspect],
  );

  const mesh = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (mesh.current) mesh.current.visible = kind === "plate" || runtime.live < 0.999;
    const u = material.uniforms;
    u.uShift.value.copy(runtime.parallax);
    u.uCropRoom.value.copy(runtime.cropRoom);
    u.uCropProduct.value.copy(runtime.cropProduct);
    u.uFocus.value.copy(runtime.focusRoom);
    u.uHover.value = runtime.hover;
    u.uShot.value = runtime.shot;
    u.uOpacity.value = kind === "beauty" ? 1 - runtime.live : 1;
  });

  return (
    <mesh
      ref={mesh}
      frustumCulled={false}
      renderOrder={kind === "plate" ? -10 : 10}
      material={material}
      onUpdate={(m) => m.layers.set(IMAGE_LAYER)}
    >
      <planeGeometry args={[2, 2]} />
    </mesh>
  );
}

/** Downloads a room's stills ahead of time. */
export function preloadRoom(room: RoomId, orient: Orientation) {
  for (const shot of ["room", "product"] as const)
    for (const kind of ["beauty", "plate", "depth"] as const) useTexture.preload(roomAsset(room, shot, kind, orient));
}
