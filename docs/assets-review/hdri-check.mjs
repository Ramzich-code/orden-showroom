const UA = { headers: { "User-Agent": "asset-survey/1.0" } };
const ids = ["studio_small_09","studio_small_08","photo_studio_loft_hall","brown_photostudio_02","symmetrical_garden_02","pretoria_gardens","lilienstein","rooitou_park"];
const html = [];
for (const id of ids) {
  const f = await (await fetch(`https://api.polyhaven.com/files/${id}`, UA)).json();
  const s = (r) => ((f.hdri?.[r]?.hdr?.size ?? 0) / 1048576).toFixed(1);
  console.log(id, "2k", s("2k"), "4k", s("4k"), "8k", s("8k"));
  html.push(`<div style="display:inline-block;width:380px;margin:4px;font:12px sans-serif"><img width=380 src="https://cdn.polyhaven.com/asset_img/thumbs/${id}.png?width=380&height=190"><br>${id}</div>`);
}
(await import("node:fs")).writeFileSync(new URL("./hdri.html", import.meta.url), html.join(""));
