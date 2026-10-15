// Offline cache for Mango.
// pygbag's Python runtime (~10 MB, versioned, never changes) is cached forever after the
// first visit, which is what makes repeat visits fast on phones. The game's own files are
// always checked with the network first (a quick "not modified" when nothing changed),
// falling back to the cached copy when offline.
const RUNTIME_CACHE = "pygbag-0.9.3";
const GAME_CACHE = "mango-game";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
    const request = event.request;
    if (request.method !== "GET") return;
    const url = new URL(request.url);

    if (url.hostname === "pygame-web.github.io") {
        event.respondWith(cacheFirst(request));
    } else if (url.origin === self.location.origin) {
        event.respondWith(networkFirst(request));
    }
});

async function cacheFirst(request) {
    const cache = await caches.open(RUNTIME_CACHE);
    const cached = await cache.match(request);
    if (cached) return cached;
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
}

async function networkFirst(request) {
    const cache = await caches.open(GAME_CACHE);
    try {
        const response = await fetch(request);
        if (response.ok) cache.put(request, response.clone());
        return response;
    } catch (error) {
        const cached = await cache.match(request);
        if (cached) return cached;
        throw error;
    }
}
