import type * as THREE from "three";
import { buildBedsideTable } from "./bedsideTable.ts";
import { buildCoffeeTable } from "./coffeeTable.ts";
import { buildWardrobe } from "./wardrobe.ts";

/**
 * Source models, one independent factory per product. `npm run models`
 * exports each to public/models/<id>.glb, which is what the site loads.
 * Keys match ProductId in src/config/products.ts.
 */
export const MODEL_BUILDERS: Record<string, () => THREE.Group> = {
  "coffee-table": buildCoffeeTable,
  "bedside-table": buildBedsideTable,
  wardrobe: buildWardrobe,
};
