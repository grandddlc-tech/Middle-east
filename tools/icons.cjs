// آیکون‌های برنامه (PNG) را با Chromium از روی شکل واقعی کشورها می‌سازد.
const fs = require("fs"), path = require("path");
const {chromium} = require("playwright");
const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const MAP = JSON.parse(html.match(/const MAP = (\{.*?\});\n/s)[1]);
const shapes = Object.values(MAP.targets).map(t => `<path d="${t.d}"/>`).join("");
// بخش کشورهای هدف: تقریباً x 40..900 و y 0..800 در نقشهٔ ۱۰۰۰×۸۲۰
function svg(size, pad) {
  const inner = size * (1 - 2 * pad), s = inner / 900, tx = size * pad - 45 * s, ty = size * pad + (inner - 790 * s) / 2 - 10 * s;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0f766e"/><stop offset=".6" stop-color="#4f46e5"/><stop offset="1" stop-color="#db2777"/></linearGradient></defs>
  <rect width="${size}" height="${size}" fill="url(#g)"/>
  <g transform="translate(${tx} ${ty}) scale(${s})" fill="#fff" fill-opacity=".93" stroke="#4f46e5" stroke-opacity=".45" stroke-width="3" stroke-linejoin="round">${shapes}</g>
  <g transform="translate(${tx} ${ty}) scale(${s})"><circle cx="735" cy="285" r="44" fill="#f59e0b" stroke="#fff" stroke-width="12"/></g>
</svg>`;
}
(async () => {
  const b = await chromium.launch(), p = await b.newPage();
  const out = [["icon-192.png",192,.1],["icon-512.png",512,.1],["icon-maskable-512.png",512,.2],["apple-touch-icon.png",180,.1],["favicon-32.png",32,.04]];
  for (const [name, size, pad] of out) {
    await p.setViewportSize({width:size, height:size});
    await p.setContent(`<body style="margin:0">${svg(size,pad)}</body>`);
    await p.screenshot({path: path.join(root, "icons", name), omitBackground: false});
  }
  fs.writeFileSync(path.join(root, "icons", "icon.svg"), svg(512,.1));
  await b.close(); console.log("icons done");
})();
