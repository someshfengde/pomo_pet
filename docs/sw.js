const CACHE_PREFIX = `pomo-pet-pwa:${self.registration.scope}:`;
const CACHE_NAME = `${CACHE_PREFIX}v20`;
const APP_SHELL = [
  "./", "./index.html", "./styles.css?v=20", "./app.js?v=20",
  "./manifest.webmanifest", "./assets/icons/icon-192.png",
  "./assets/icons/icon-512.png", "./assets/preview.png",
  "./assets/pets/avacado/spritesheet.webp",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME).map((key) => caches.delete(key)),
  )).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  // Do not cache unrelated apps, external pet APIs, or unbounded remote images.
  if (url.origin !== self.location.origin || !url.href.startsWith(self.registration.scope)) return;
  const navigation = event.request.mode === "navigate";
  const fresh = navigation || ["script", "style", "worker"].includes(event.request.destination) || url.pathname.endsWith(".webmanifest");
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const key = navigation ? "./index.html" : event.request;
    const cached = await cache.match(key);
    if (!fresh && cached) return cached;
    try {
      const response = await fetch(event.request);
      if (response.ok && (navigation || APP_SHELL.some((asset) => new URL(asset, self.registration.scope).href === url.href))) {
        await cache.put(key, response.clone());
      }
      return response.ok ? response : cached || response;
    } catch {
      return cached || Response.error();
    }
  })());
});
