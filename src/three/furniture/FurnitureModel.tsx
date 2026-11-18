"use client";

import { Fragment, RefObject, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { createPortal, useFrame } from "@react-three/fiber";
import { Html, useGLTF } from "@react-three/drei";
import type { FinishId, MaterialRole, Product, ProductComponent } from "@/config/products";
import { getMaterial } from "../materials";

interface FurnitureModelProps {
  product: Product;
  finish: FinishId;
  /** 0 = assembled, 1 = fully exploded. Read every frame, so it can be tweened. */
  explodeRef?: RefObject<number>;
  /** Show the technical labels of the annotated components. */
  labels?: boolean;
  /**
   * Overlay copy for a finish crossfade: own transparent materials whose
   * opacity follows this ref (drawn over the new finish, same geometry).
   */
  fadeRef?: RefObject<number>;
}

type PartData = { base: THREE.Vector3; explode: THREE.Vector3; delay: number };

/** Parts leave one after another (in catalogue order) and come back in reverse. */
const STAGGER = 0.4;
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

/**
 * A product from its GLB. Materials come from each component's role (glTF
 * extras, see blender/products/export_glb.py); the exploded view offsets the
 * component nodes. Geometry is never modified.
 */
export function FurnitureModel({ product, finish, explodeRef, labels = false, fadeRef }: FurnitureModelProps) {
  const { scene } = useGLTF(product.model);
  const object = useMemo(() => scene.clone(true), [scene]);
  const byId = useMemo(() => new Map(product.components.map((c) => [c.id, c])), [product]);
  const order = useMemo(() => new Map(product.components.map((c, i) => [c.id, i / Math.max(1, product.components.length - 1)])), [product]);
  const fadeMaterials = useRef<THREE.Material[]>([]);
  const parts = useRef<{ node: THREE.Object3D; data: PartData }[]>([]);
  const [annotated, setAnnotated] = useState<{ node: THREE.Object3D; component: ProductComponent }[]>([]);

  useLayoutEffect(() => {
    parts.current = [];
    const notes: { node: THREE.Object3D; component: ProductComponent }[] = [];
    object.traverse((o) => {
      const c = byId.get(o.name);
      if (!c) return;
      parts.current.push({
        node: o,
        data: { base: o.position.clone(), explode: new THREE.Vector3(...c.explode), delay: (order.get(c.id) ?? 0) * STAGGER },
      });
      if (c.annotate) notes.push({ node: o, component: c });
    });
    setAnnotated(notes);
  }, [object, byId, order]);

  useLayoutEffect(() => {
    const fades: THREE.Material[] = [];
    object.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      let n: THREE.Object3D | null = mesh;
      while (n && !n.userData.role) n = n.parent;
      const role = (n?.userData.role ?? "body") as MaterialRole;
      let m = getMaterial(product, finish, role);
      if (fadeRef) {
        m = m.clone();
        m.transparent = true;
        m.depthWrite = false;
        m.depthFunc = THREE.LessEqualDepth;
        fades.push(m);
        mesh.renderOrder = 2;
      }
      mesh.material = m;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
    });
    fadeMaterials.current = fades;
    return () => fades.forEach((m) => m.dispose());
  }, [object, product, finish, fadeRef]);

  useFrame(() => {
    const p = explodeRef?.current ?? 0;
    for (const { node, data } of parts.current) {
      const local = easeInOut(THREE.MathUtils.clamp((p - data.delay) / (1 - STAGGER), 0, 1));
      node.position.copy(data.base).addScaledVector(data.explode, local);
    }
    if (fadeRef) for (const m of fadeMaterials.current) m.opacity = fadeRef.current ?? 0;
  });

  return (
    <>
      <primitive object={object} />
      {!fadeRef && annotated.map(({ node, component }) => (
        <Fragment key={component.id}>
          {createPortal(
          <Html center zIndexRange={[20, 5]} className="pointer-events-none">
            <span className="part-label" data-on={labels || undefined}>
              <span className="part-label-name">{component.label}</span>
              {component.detail && <span className="part-label-detail">{component.detail}</span>}
            </span>
          </Html>,
          node,
          )}
        </Fragment>
      ))}
    </>
  );
}
