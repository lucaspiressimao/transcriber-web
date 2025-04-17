self.addEventListener('install', function (event) {
    console.log('[ServiceWorker] Install');
    self.skipWaiting();
});

self.addEventListener('fetch', function (event) {
    event.respondWith(fetch(event.request));
});
