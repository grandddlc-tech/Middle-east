// نقشه‌ها را از داده‌های Natural Earth (بستهٔ world-atlas) به مسیرهای SVG تبدیل می‌کند
// و همراه داده‌های اروپا در src/template.html تزریق می‌کند تا index.html ساخته شود.
// Builds the SVG maps for each region (Middle East, Europe) and injects them into src/template.html.
import fs from "fs";
import {feature, merge} from "topojson-client";
import {geoMercator, geoConicConformal, geoPath} from "d3-geo";

const t = JSON.parse(fs.readFileSync(new URL("./node_modules/world-atlas/countries-50m.json", import.meta.url)));
const geoms = t.objects.countries.geometries;
const byName = n => { const g = geoms.filter(g => g.properties.name === n); if (!g.length) throw new Error("missing " + n); return g; };

// کریمه در این داده جزو روسیه است؛ طبق مرز شناخته‌شدهٔ بین‌المللی آن را به اوکراین برمی‌گردانیم
// Crimea is drawn as part of Russia in this dataset; move it to Ukraine (internationally recognized border)
{
  const ru = byName("Russia")[0], ua = byName("Ukraine")[0];
  const crimea = ru.arcs.findIndex(poly => {
    const f = feature(t, {type:"Polygon", arcs:poly});
    return f.geometry.coordinates[0].every(([x,y]) => x > 32.4 && x < 36.7 && y > 44.3 && y < 46.3);
  });
  if (crimea < 0) throw new Error("Crimea polygon not found");
  const poly = ru.arcs.splice(crimea, 1)[0];
  if (ua.type === "Polygon"){ ua.type = "MultiPolygon"; ua.arcs = [ua.arcs]; }
  ua.arcs.push(poly);
}

const REGIONS = {
  me: {
    W: 1000,
    targets: {ir:"Iran",iq:"Iraq",tr:"Turkey",sy:"Syria",lb:"Lebanon",jo:"Jordan",ps:"Palestine",il:"Israel",
      sa:"Saudi Arabia",kw:"Kuwait",bh:"Bahrain",qa:"Qatar",ae:"United Arab Emirates",om:"Oman",ye:"Yemen",eg:"Egypt",cy:["Cyprus","N. Cyprus"]},
    proj: () => geoMercator(),
    fit: {type:"MultiPoint", coordinates:[[24.2,11.2],[63.6,11.2],[63.6,42.6],[24.2,42.6]]}, H: 820,
    caps: {ir:[51.389,35.6892], iq:[44.3661,33.3152], tr:[32.8597,39.9334], sy:[36.2765,33.5138], lb:[35.5018,33.8938], jo:[35.9284,31.9454],
      ps:[35.2333,31.7833], il:[35.2137,31.7683], sa:[46.6753,24.7136], kw:[47.9774,29.3759], bh:[50.586,26.2285], qa:[51.531,25.2854],
      ae:[54.3773,24.4539], om:[58.3829,23.588], ye:[44.191,15.3694], eg:[31.2357,30.0444], cy:[33.3823,35.1856]},
    // label: [lon,lat] of the text, anchor: [lon,lat] for a leader line
    labels: {lb:{p:[34.3,33.6],a:[35.6,33.8]}, il:{p:[33.35,32.6],a:[34.95,32.4]}, ps:{p:[33.25,31.75],a:[35.2,31.9]},
      bh:{p:[50.0,27.1],a:[50.55,26.1]}, om:{p:[56.8,21.2]}, cy:{p:[33.1,35.15]}},
    seas: [["دریای مدیترانه","Mediterranean Sea",29,34],["دریای سرخ","Red Sea",38.5,20,-58],["خلیج فارس","Persian Gulf",53.1,26.4,-35],
      ["دریای خزر","Caspian Sea",51,41.5],["دریای عرب","Arabian Sea",62,18],["خلیج عدن","Gulf of Aden",48.3,12.4],["دریای سیاه","Black Sea",34,42.2],["دریای عمان","Gulf of Oman",58.9,24.4,-30]]
  },
  ea: {
    W: 1000,
    targets: {cn:["China","Hong Kong","Macao"], jp:"Japan", kr:"South Korea", kp:"North Korea", mn:"Mongolia", tw:"Taiwan"},
    proj: () => geoConicConformal().parallels([25, 47]).rotate([-110, 0]),
    fit: {type:"MultiPoint", coordinates:[[73,40],[78,30],[96,21],[110,18],[122,21],[146,30],[146,45],[132,53],[110,53],[90,51]]},
    caps: {cn:[116.4074,39.9042], jp:[139.6917,35.6895], kr:[126.978,37.5665], kp:[125.7625,39.0392], mn:[106.9057,47.8864], tw:[121.5654,25.033]},
    labels: {kr:{p:[127.9,36.2]}, kp:{p:[127.0,40.2]}, tw:{p:[124.8,23.2],a:[121.0,23.8]}},
    seas: [["دریای ژاپن (دریای شرق)","Sea of Japan (East Sea)",134.5,40.5],["دریای زرد","Yellow Sea",123.3,35.6],["دریای چین شرقی","East China Sea",125.5,29.5],
      ["اقیانوس آرام","Pacific Ocean",143,30],["دریای چین جنوبی","South China Sea",115,19.5]]
  },
  sea: {
    W: 1000,
    targets: {id:"Indonesia", my:"Malaysia", sg:"Singapore", th:"Thailand", vn:"Vietnam", ph:"Philippines", mm:"Myanmar", kh:"Cambodia", la:"Laos", bn:"Brunei", tl:"Timor-Leste"},
    proj: () => geoMercator(),
    fit: {type:"MultiPoint", coordinates:[[92,-11],[141.5,-11],[141.5,28.6],[92,28.6]]},
    caps: {id:[106.8456,-6.2088], my:[101.6869,3.139], sg:[103.8198,1.3521], th:[100.5018,13.7563], vn:[105.8342,21.0278], ph:[120.9842,14.5995],
      mm:[96.1297,19.7633], kh:[104.8921,11.5564], la:[102.6331,17.9757], bn:[114.9398,4.9031], tl:[125.5603,-8.5569]},
    labels: {mm:{p:[97.8,22.3]}, sg:{p:[105.8,-0.4],a:[103.82,1.35]}, bn:{p:[112.6,6.9],a:[114.7,4.6]}, tl:{p:[126.6,-10.3],a:[125.9,-8.9]}, la:{p:[103.2,19.4]}, kh:{p:[104.9,12.8]}},
    seas: [["دریای چین جنوبی","South China Sea",113,12],["دریای آندامان","Andaman Sea",95.8,10.5],["خلیج تایلند","Gulf of Thailand",101.6,9.5,-60],
      ["دریای تیمور","Timor Sea",129,-10.8],["دریای جاوه","Java Sea",111,-5],["دریای فیلیپین","Philippine Sea",132,16]]
  },
  sa: {
    W: 1000,
    targets: {in:"India", pk:"Pakistan", bd:"Bangladesh", lk:"Sri Lanka", np:"Nepal", bt:"Bhutan", mv:"Maldives", af:"Afghanistan"},
    proj: () => geoMercator(),
    fit: {type:"MultiPoint", coordinates:[[60,-1],[97.5,-1],[97.5,38.6],[60,38.6]]},
    caps: {in:[77.209,28.6139], pk:[73.0479,33.6844], bd:[90.4125,23.8103], lk:[79.9022,6.8868], np:[85.324,27.7172], bt:[89.6386,27.4728], mv:[73.5093,4.1755], af:[69.2075,34.5553]},
    labels: {mv:{p:[68.6,1.6],a:[73.3,3.6]}, bt:{p:[92.3,29.6],a:[90.4,27.4]}, np:{p:[84.0,28.3]}},
    seas: [["دریای عرب","Arabian Sea",65,15],["خلیج بنگال","Bay of Bengal",89,15],["اقیانوس هند","Indian Ocean",84,2]]
  },
  ca: {
    W: 1000,
    targets: {kz:"Kazakhstan", uz:"Uzbekistan", tm:"Turkmenistan", kg:"Kyrgyzstan", tj:"Tajikistan", ge:"Georgia", am:"Armenia", az:"Azerbaijan"},
    proj: () => geoConicConformal().parallels([38, 50]).rotate([-62, 0]),
    fit: {type:"MultiPoint", coordinates:[[39.5,41],[41,38.5],[52,35.5],[62,35],[75,36.5],[88,46],[87,50],[78,54.5],[62,56],[50,52.5],[46,47]]},
    caps: {kz:[71.4704,51.1605], uz:[69.2401,41.2995], tm:[58.3261,37.9601], kg:[74.5698,42.8746], tj:[68.7791,38.5598], ge:[44.8271,41.7151], am:[44.5152,40.1872], az:[49.8671,40.4093]},
    labels: {am:{p:[43.4,38.6],a:[44.9,40.2]}, ge:{p:[43.6,42.3]}, az:{p:[48.0,40.6]}, tj:{p:[70.5,38.6]}, kg:{p:[74.6,41.6]}},
    seas: [["دریای خزر","Caspian Sea",51,42],["دریاچهٔ آرال","Aral Sea",59.6,45.2],["دریای سیاه","Black Sea",40.3,43.3]]
  },
  eu: {
    W: 1000,
    targets: {al:"Albania", ad:"Andorra", at:"Austria", by:"Belarus", be:"Belgium", ba:"Bosnia and Herz.", bg:"Bulgaria", hr:"Croatia",
      cz:"Czechia", dk:"Denmark", ee:"Estonia", fi:"Finland", fr:"France", de:"Germany", gr:"Greece", hu:"Hungary", is:"Iceland", ie:"Ireland",
      it:"Italy", lv:"Latvia", li:"Liechtenstein", lt:"Lithuania", lu:"Luxembourg", mt:"Malta", md:"Moldova", mc:"Monaco", me:"Montenegro",
      nl:"Netherlands", mk:"Macedonia", no:"Norway", pl:"Poland", pt:"Portugal", ro:"Romania", ru:"Russia", sm:"San Marino", rs:"Serbia",
      sk:"Slovakia", si:"Slovenia", es:"Spain", se:"Sweden", ch:"Switzerland", ua:"Ukraine", gb:"United Kingdom", va:"Vatican"},
    proj: () => geoConicConformal().parallels([40, 64]).rotate([-14, 0]),
    fit: {type:"MultiPoint", coordinates:[[-24.5,63.3],[-24.5,66.6],[-10,35.5],[14.5,35.7],[28,34.8],[14.5,34.4],[46,44],[46,60],[30,70.3],[18,70.5],[-9.5,52]]},
    caps: {al:[19.8187,41.3275], ad:[1.5218,42.5063], at:[16.3738,48.2082], by:[27.5615,53.9045], be:[4.3517,50.8503], ba:[18.4131,43.8563],
      bg:[23.3219,42.6977], hr:[15.9819,45.815], cz:[14.4378,50.0755], dk:[12.5683,55.6761], ee:[24.7536,59.437], fi:[24.9384,60.1699],
      fr:[2.3522,48.8566], de:[13.405,52.52], gr:[23.7275,37.9838], hu:[19.0402,47.4979], is:[-21.9426,64.1466], ie:[-6.2603,53.3498],
      it:[12.4964,41.9028], lv:[24.1052,56.9496], li:[9.5209,47.141], lt:[25.2797,54.6872], lu:[6.1296,49.6116], mt:[14.5146,35.8989],
      md:[28.8638,47.0105], mc:[7.4246,43.7384], me:[19.2594,42.4304], nl:[4.9041,52.3676], mk:[21.4314,41.9981], no:[10.7522,59.9139],
      pl:[21.0122,52.2297], pt:[-9.1393,38.7223], ro:[26.1025,44.4268], ru:[37.6173,55.7558], sm:[12.4469,43.9424], rs:[20.4489,44.7866],
      sk:[17.1077,48.1486], si:[14.5058,46.0569], es:[-3.7038,40.4168], se:[18.0686,59.3293], ch:[7.4474,46.948], ua:[30.5234,50.4501],
      gb:[-0.1276,51.5072], va:[12.4534,41.9029]},
    labels: {ad:{p:[-1.2,44.2],a:[1.55,42.55]}, mc:{p:[6.2,42.2],a:[7.42,43.74]}, sm:{p:[14.8,44.6],a:[12.45,43.94]}, va:{p:[10.3,40.6],a:[12.45,41.9]},
      li:{p:[7.6,48.9],a:[9.55,47.15]}, lu:{p:[4.4,50.0],a:[6.1,49.75]}, mt:{p:[14.4,34.9],a:[14.45,35.9]}, me:{p:[18.0,41.7],a:[19.2,42.75]},
      al:{p:[18.4,40.6],a:[20.0,41.0]}, mk:{p:[21.7,41.6]}, ba:{p:[17.8,44.2]}, si:{p:[14.8,46.1]}, ru:{p:[39.5,57.5]}, no:{p:[9.5,61.4]},
      be:{p:[4.5,50.65]}, nl:{p:[5.6,52.3]}, dk:{p:[9.2,56.1]}, gr:{p:[22.2,39.4]}, hr:{p:[15.6,45.35]}},
    seas: [["اقیانوس اطلس","Atlantic Ocean",-13.5,45.5],["دریای شمال","North Sea",3,56.5],["دریای بالتیک","Baltic Sea",19.3,56.5,-60],
      ["دریای مدیترانه","Mediterranean Sea",6,38.5],["دریای سیاه","Black Sea",34,43.4],["دریای نروژ","Norwegian Sea",2,66.5]]
  }
};

const fix = v => +v.toFixed(1);
const maps = {};
for (const [rid, R] of Object.entries(REGIONS)) {
  const proj = R.proj();
  let W = R.W, H = R.H;
  if (H) proj.fitExtent([[0,0],[W,H]], R.fit);
  else { proj.fitWidth(W, R.fit); const b = geoPath(proj).bounds(R.fit); H = Math.round(b[1][1] + b[0][1]); }
  proj.clipExtent([[-20,-20],[W+20,H+20]]);
  const path = geoPath(proj).digits(1), P = ll => proj(ll).map(fix);
  const out = {W, H, targets:{}, others:"", caps:{}, ll:R.caps, lbl:{}, seas:[]};
  const taken = new Set();
  for (const [k, n] of Object.entries(R.targets)) {
    const names = [].concat(n); names.forEach(x => taken.add(x));
    const f = {type:"Feature", geometry: merge(t, names.flatMap(byName))};
    const c = path.centroid(f), b = path.bounds(f);
    out.targets[k] = {d: path(f), c: c.map(fix), r: Math.round(Math.max(b[1][0]-b[0][0], b[1][1]-b[0][1]))};
  }
  out.others = geoms.filter(g => !taken.has(g.properties.name)).map(g => path(feature(t, g)) || "").join("");
  for (const [k, ll] of Object.entries(R.caps)) out.caps[k] = P(ll);
  for (const [k, L] of Object.entries(R.labels)) out.lbl[k] = {p: P(L.p), ...(L.a ? {a: P(L.a)} : {})};
  out.seas = R.seas.map(([fa, en, lon, lat, rot]) => [fa, en, ...P([lon, lat]), rot || 0]);
  maps[rid] = out;
  console.log(rid, W + "x" + H, Math.round(JSON.stringify(out).length/1024) + " KB");
}

const root = new URL("../", import.meta.url);
const tpl = fs.readFileSync(new URL("src/template.html", root), "utf8");
const data = ["europe.js", "europe_words.js", "asia.js", "asia_words.js"].map(f => fs.readFileSync(new URL("src/" + f, root), "utf8")).join("\n");
fs.writeFileSync(new URL("index.html", root), tpl.replace("/*MAP_DATA*/", JSON.stringify(maps)).replace("/*REGION_DATA*/", () => data));
console.log("index.html built");
