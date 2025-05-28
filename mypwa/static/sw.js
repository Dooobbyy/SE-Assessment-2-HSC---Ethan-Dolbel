self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open('my-pwa-cache').then(function(cache) {
      return cache.addAll([
        '/',
        '/static/icon.png',
        '/manifest.json'
      ]);
    })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});