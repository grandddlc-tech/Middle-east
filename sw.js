// کش آفلاین: فایل‌های برنامه یک‌بار ذخیره می‌شوند و بعد بدون اینترنت هم کار می‌کند.
// با هر تغییر در فایل‌ها، VERSION را بالا ببرید تا نسخهٔ تازه جایگزین شود.
const VERSION = "v8";
const CACHE = "me-game-" + VERSION;
const FILES = ["./", "index.html", "manifest.webmanifest", "fonts/Vazirmatn-Variable.woff2",
  "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "icons/apple-touch-icon.png", "icons/favicon-32.png",
  "audio/list.json"];

self.addEventListener("install", e => {
  // the app files first, then every word's audio (listed in audio/list.json); a missing audio file doesn't block the install
  e.waitUntil(caches.open(CACHE).then(async c => {
    await c.addAll(FILES);
    const list = await (await c.match("audio/list.json")).json();
    await Promise.allSettled(list.map(f => c.add("audio/" + f)));
  }).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  // صفحهٔ اصلی: اول از شبکه (تا نسخهٔ تازه زود برسد)، بدون اینترنت از کش
  if (req.mode === "navigate"){
    e.respondWith(fetch(req).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put("index.html", copy)); return r; })
      .catch(() => caches.match("index.html")));
    return;
  }
  // بقیهٔ فایل‌ها: اول از کش، و در پس‌زمینه به‌روزرسانی از شبکه
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(req, {ignoreSearch: true});
    const net = fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
