// Builds candidates.json + candidates.html from Poly Haven / ambientCG public APIs (metadata only).
import { writeFileSync } from "node:fs";
const UA = { headers: { "User-Agent": "asset-survey/1.0" } };
const get = (u) => fetch(u, UA).then((r) => r.json());

const PH = {
  "Walnut (coffee table platform)": ["american_walnut_veneer","black_walnut_veneer_01","black_walnut_veneer_02","black_walnut_veneer_03","european_walnut_veneer_04","european_walnut_veneer_05","natural_walnut_veneer","smoked_walnut_veneer","walnut_veneer","walnut_veneer_02"],
  "Oak (Natural Oak finish)": ["oak_veneer_01","oak_veneer_02","oak_veneer_03","oak_veneer_04","oak_veneer_05","white_oak_veneer"],
  "Marble (Poly Haven)": ["marble_01"],
  "Floor": ["oak_wood_planks","wood_floor","laminate_floor_02","laminate_floor_03","plank_flooring_02","plank_flooring_03","plank_flooring_04","wooden_floor_01","wooden_floor_02","rectangular_parquet"],
  "Walls": ["painted_plaster_wall","white_plaster_02","plastered_wall_02","plastered_wall_03","plastered_wall_04","plastered_wall_05","white_stucco","beige_wall_001","beige_wall_002","clay_plaster","white_rough_plaster"],
  "Fabrics": ["wool_boucle","curly_teddy_natural","rough_linen","hessian_230"],
};
const PH_MODELS = ["Sofa_01","sofa_02","sofa_03","ArmChair_01","mid_century_lounge_chair","potted_plant_01","potted_plant_02","potted_plant_04","pachira_aquatica_01","calathea_orbifolia_01","ceramic_vase_01","ceramic_vase_02","ceramic_vase_03","ceramic_vase_04","antique_ceramic_vase_01","decorative_book_set_01","book_encyclopedia_set_01","wooden_bowl_01","wooden_bowl_02","ceramic_pot","planter_pot_clay"];
const ACG = {
  "Travertine (coffee table top)": Array.from({ length: 14 }, (_, i) => `Travertine${String(i + 1).padStart(3, "0")}`),
  "White marble (bedside top)": ["Marble002","Marble005","Marble006","Marble007","Marble008","Marble009","Marble012","Marble014","Marble015","Marble016","Marble017","Marble018","Marble019","Marble020","Marble021","Marble023","Marble024","Marble025"],
  "Rug": ["Carpet001","Carpet002","Carpet003","Carpet004","Carpet005","Carpet006","Carpet008","Carpet011","Carpet012","Carpet013","Carpet014","Carpet015","Carpet016"],
  "Surface imperfections": ["Fingerprints001","Fingerprints002","Fingerprints003","Fingerprints004","Fingerprints005","Fingerprints006","Smear002","Smear003","Smear004"],
};

const mb = (b) => (b / 1048576).toFixed(1) + " MB";
const sumMaps = (files, res, keys) => {
  let total = 0;
  for (const k of keys) {
    const m = files[k]?.[res]; if (!m) continue;
    const f = m.jpg || m.png || m.exr; if (f) total += f.size;
  }
  return total;
};
const out = [];
const phAll = await get("https://api.polyhaven.com/assets");
for (const [group, ids] of Object.entries(PH)) for (const id of ids) {
  const files = await get(`https://api.polyhaven.com/files/${id}`);
  const keys = ["Diffuse","Rough","nor_gl","Displacement"];
  out.push({ group, id, name: phAll[id]?.name ?? id, source: "Poly Haven", license: "CC0", page: `https://polyhaven.com/a/${id}`,
    preview: `https://cdn.polyhaven.com/asset_img/thumbs/${id}.png?width=256&height=256`,
    size2k: mb(sumMaps(files, "2k", keys)), size4k: mb(sumMaps(files, "4k", keys)), maps: "Color, Roughness, Normal (GL), Displacement" });
}
for (const id of PH_MODELS) {
  const files = await get(`https://api.polyhaven.com/files/${id}`);
  const g = files.gltf?.["2k"]?.gltf; let total = g ? g.size : 0;
  if (g?.include) for (const f of Object.values(g.include)) total += f.size;
  out.push({ group: "Decor models", id, name: phAll[id]?.name ?? id, source: "Poly Haven", license: "CC0", page: `https://polyhaven.com/a/${id}`,
    preview: `https://cdn.polyhaven.com/asset_img/thumbs/${id}.png?width=256&height=256`, size2k: mb(total), size4k: "—", maps: "glTF + 2K PBR textures" });
}
for (const [group, ids] of Object.entries(ACG)) {
  const j = await get(`https://ambientcg.com/api/v2/full_json?id=${ids.join(",")}&include=downloadData,imageData`);
  for (const a of j.foundAssets) {
    const dl = a.downloadFolders?.default?.downloadFiletypeCategories?.zip?.downloads ?? [];
    const s = (att) => { const d = dl.find((x) => x.attribute === att); return d ? mb(d.size) : "—"; };
    out.push({ group, id: a.assetId, name: a.assetId, source: "ambientCG", license: "CC0", page: `https://ambientcg.com/view?id=${a.assetId}`,
      preview: a.previewImage?.["256-PNG"], size2k: s("2K-JPG"), size4k: s("4K-JPG"), maps: "Color, Roughness, Normal (GL), Displacement (zip)" });
  }
}
// HDRIs: studios for product renders, sunny outdoor for the window view
const hd = await get("https://api.polyhaven.com/assets?t=hdris");
const pick = Object.entries(hd).filter(([k, v]) => /studio/.test(k) && !/christmas|colorful|blue/.test(k)).slice(0, 14)
  .concat(Object.entries(hd).filter(([k, v]) => (v.tags || []).some((t) => /garden|park/.test(t)) && (v.categories || []).includes("sunrise-sunset") === false && (v.categories || []).includes("outdoor")).slice(0, 14));
for (const [id, v] of pick) {
  const files = await get(`https://api.polyhaven.com/files/${id}`);
  out.push({ group: /studio/.test(id) ? "HDRI — product studio" : "HDRI — window exterior", id, name: v.name, source: "Poly Haven", license: "CC0",
    page: `https://polyhaven.com/a/${id}`, preview: `https://cdn.polyhaven.com/asset_img/thumbs/${id}.png?width=256&height=128`,
    size2k: mb(files.hdri?.["2k"]?.hdr?.size ?? 0), size4k: mb(files.hdri?.["4k"]?.hdr?.size ?? 0), maps: "HDR" });
}
writeFileSync(new URL("./candidates.json", import.meta.url), JSON.stringify(out, null, 1));
const groups = [...new Set(out.map((o) => o.group))];
const html = `<!doctype html><meta charset=utf-8><title>ORDEN asset candidates</title><style>body{font:13px system-ui;background:#f4f0e8;margin:24px}h2{margin:28px 0 10px}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}.c{background:#fff;padding:8px}img{width:100%;display:block;background:#ddd}b{display:block;margin-top:6px}</style>
<h1>Candidates (metadata only, nothing downloaded)</h1>${groups.map((g) => `<h2>${g}</h2><div class=g>${out.filter((o) => o.group === g).map((o) => `<div class=c><img src="${o.preview}" loading=lazy><b>${o.id}</b>${o.source} · ${o.size2k} / ${o.size4k}</div>`).join("")}</div>`).join("")}`;
writeFileSync(new URL("./candidates.html", import.meta.url), html);
console.log("candidates:", out.length, "groups:", groups.join(" | "));
