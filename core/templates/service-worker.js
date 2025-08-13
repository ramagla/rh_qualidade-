/* Service Worker – Bras-Mol (network-first p/ páginas, cache-first p/ estáticos) */
const SW_VERSION = "bm-pwa-v1";
const RUNTIME_CACHE = `${SW_VERSION}-dynamic`;
const STATIC_CACHE = `${SW_VERSION}-static`;

/* Liste aqui (opcional) estáticos que sempre quer em cache ao instalar */
const CORE_ASSETS = [
  "/",                    // homepage
  "/manifest.webmanifest" // manifesto
  // Adicione aqui seus CSS/JS críticos se quiser pré-cache
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(CORE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => ![STATIC_CACHE, RUNTIME_CACHE].includes(k))
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

function isNavigationRequest(request) {
  return request.mode === "navigate" || (request.method === "GET" && request.headers.get("accept")?.includes("text/html"));
}
function isStaticAsset(request) {
  const url = new URL(request.url);
  return (
    url.pathname.startsWith("/static/") ||
    /\.(?:css|js|png|jpg|jpeg|gif|webp|svg|ico|woff2?|ttf|eot|map)$/.test(url.pathname)
  );
}

self.addEventListener("fetch", (event) => {
  const req = event.request;

  // Navegação (páginas): network-first com fallback para cache
  if (isNavigationRequest(req)) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const clone = res.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(req, clone));
          return res;
        })
        .catch(() =>
          caches.match(req).then((cached) => cached || caches.match("/"))
        )
    );
    return;
  }

  // Estáticos: cache-first com atualização em background
  if (isStaticAsset(req)) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const fetchAndUpdate = fetch(req)
          .then((res) => {
            const clone = res.clone();
            caches.open(STATIC_CACHE).then((cache) => cache.put(req, clone));
            return res;
          })
          .catch(() => cached); // se offline, usa o que tiver

        return cached || fetchAndUpdate;
      })
    );
    return;
  }

  // Demais requests: tenta rede, cai para cache
  event.respondWith(
    fetch(req)
      .then((res) => {
        const clone = res.clone();
        caches.open(RUNTIME_CACHE).then((cache) => cache.put(req, clone));
        return res;
      })
      .catch(() => caches.match(req))
  );
});
