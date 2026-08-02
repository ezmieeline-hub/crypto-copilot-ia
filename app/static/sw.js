const CACHE = "crypto-copilot-v6";

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE).then(cache =>
            cache.addAll([
                "/",
                "/static/app.css",
                "/static/app.js"
            ])
        )
    );
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE)
                    .map(key => caches.delete(key))
            )
        )
    );
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
