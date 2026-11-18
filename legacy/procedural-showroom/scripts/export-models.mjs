/**
 * Exports every model factory in src/three/models to public/models/<id>.glb.
 * Run with `npm run models` after editing a model. Requires Node 22.18+ / 23.6+
 * (native TypeScript type stripping).
 *
 * A 3D artist can replace any of these files with a refined GLB, as long as
 * node names match the component ids in src/config/products.ts.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// GLTFExporter reads Blobs through FileReader, which Node does not provide.
globalThis.FileReader ??= class {
  readAsArrayBuffer(blob) {
    blob.arrayBuffer().then((buf) => {
      this.result = buf;
      this.onloadend?.();
    });
  }
};

const { GLTFExporter } = await import("three/addons/exporters/GLTFExporter.js");
const { MODEL_BUILDERS } = await import("../src/three/models/index.ts");

const out = join(dirname(fileURLToPath(import.meta.url)), "..", "public", "models");
mkdirSync(out, { recursive: true });

const exporter = new GLTFExporter();
for (const [id, build] of Object.entries(MODEL_BUILDERS)) {
  const model = build();
  const glb = await exporter.parseAsync(model, { binary: true });
  const file = join(out, `${id}.glb`);
  writeFileSync(file, Buffer.from(glb));
  const parts = model.children.map((c) => c.name).join(", ");
  console.log(`✓ ${id}.glb  ${(glb.byteLength / 1024).toFixed(0)} KB  [${parts}]`);
}
