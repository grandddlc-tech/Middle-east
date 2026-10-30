// نقشه را از داده‌های Natural Earth (بستهٔ world-atlas) به مسیرهای SVG تبدیل می‌کند
// و در src/template.html تزریق می‌کند تا index.html تک‌فایلی ساخته شود.
import fs from "fs";
import {feature, merge} from "topojson-client";
import {geoMercator, geoPath} from "d3-geo";

const t = JSON.parse(fs.readFileSync(new URL("./node_modules/world-atlas/countries-50m.json", import.meta.url)));
const geoms = t.objects.countries.geometries;
const byName = n => geoms.filter(g => g.properties.name === n);
const targets = {ir:"Iran",iq:"Iraq",tr:"Turkey",sy:"Syria",lb:"Lebanon",jo:"Jordan",ps:"Palestine",il:"Israel",
  sa:"Saudi Arabia",kw:"Kuwait",bh:"Bahrain",qa:"Qatar",ae:"United Arab Emirates",om:"Oman",ye:"Yemen",eg:"Egypt",cy:"Cyprus"};
const W = 1000, H = 820;
const proj = geoMercator().fitExtent([[0,0],[W,H]], {type:"MultiPoint",
  coordinates:[[24.2,11.2],[63.6,11.2],[63.6,42.6],[24.2,42.6]]});
proj.clipExtent([[-20,-20],[W+20,H+20]]);
const path = geoPath(proj).digits(1);

const out = {W, H, targets:{}, others:""};
for (const [k,n] of Object.entries(targets)) {
  let gs = byName(n);
  if (k === "cy") gs = gs.concat(byName("N. Cyprus")); // کل جزیره (مرز شناخته‌شدهٔ بین‌المللی)
  const f = {type:"Feature", geometry: merge(t, gs)};
  const c = path.centroid(f), b = path.bounds(f);
  out.targets[k] = {d: path(f), c: c.map(v => +v.toFixed(1)), r: Math.round(Math.max(b[1][0]-b[0][0], b[1][1]-b[0][1]))};
}
const taken = new Set(Object.values(targets).concat("N. Cyprus"));
out.others = geoms.filter(g => !taken.has(g.properties.name)).map(g => path(feature(t, g)) || "").join("");

const root = new URL("../", import.meta.url);
const tpl = fs.readFileSync(new URL("src/template.html", root), "utf8");
fs.writeFileSync(new URL("index.html", root), tpl.replace("/*MAP_DATA*/", JSON.stringify(out)));
console.log("index.html built");
