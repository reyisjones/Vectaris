/**
 * Vectaris Service Worker
 * 
 * Caching strategy:
 * - App shell (HTML, JS, CSS): cache-first with network fallback
 * - API responses: network-first with cache fallback
 * - Images: cache-first
 * 
 * Offline behavior: serve cached API responses when network unavailable.
 */

const CACHE_VERSION = "vectaris-v1.0.0";
const CACHE_STATIC = `${CACHE_VERSION}-static`;
const CACHE_API = `${CACHE_VERSION}-api`;

const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
];

// Install: cache static assets
self.addEventListener("install", (event) => {
  console.log("[SW] Installing service worker...");
  event.waitUntil(
    caches.open(CACHE_STATIC).then((cache) => {
      console.log("[SW] Caching static assets");
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener("activate", (event) => {
  console.log("[SW] Activating service worker...");
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key.startsWith("vectaris-") && key !== CACHE_STATIC && key !== CACHE_API) {
            console.log("[SW] Deleting old cache:", key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch: handle requests
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== "GET") {
    return;
  }

  // API requests: network-first, cache fallback
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone and cache successful responses
          if (response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_API).then((cache) => {
              cache.put(request, clone);
            });
          }
          return response;
        })
        .catch(() => {
          // Network failed — try cache
          return caches.match(request).then((cached) => {
            if (cached) {
              console.log("[SW] Serving cached API response:", url.pathname);
              return cached;
            }
            // Return minimal error response
            return new Response(
              JSON.stringify({ error: "Offline", detail: "No cached data available" }),
              {
                status: 503,
                headers: { "Content-Type": "application/json" },
              }
            );
          });
        })
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(request).then((response) => {
        // Cache successful responses
        if (response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_STATIC).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      });
    })
  );
});
