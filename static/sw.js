/* MediAssist AI - service worker
   Caches static assets for offline/instant loading; network-first for pages.
   Scope: / (served from the /sw.js root route). */
const CACHE = 'medassist-v1';
const CORE_ASSETS = [
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.webmanifest',
  '/static/images/icon.svg',
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return cache.addAll(CORE_ASSETS);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== CACHE; })
            .map(function (k) { return caches.delete(k); })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Pages: network first, fall back to cached landing page when offline.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (cache) { cache.put('/', copy); });
        return res;
      }).catch(function () {
        return caches.match('/');
      })
    );
    return;
  }

  // Static assets: cache first, then network + cache.
  event.respondWith(
    caches.match(req).then(function (cached) {
      return cached || fetch(req).then(function (res) {
        if (res.ok && (url.pathname.indexOf('/static/') === 0)) {
          var copy = res.clone();
          caches.open(CACHE).then(function (cache) { cache.put(req, copy); });
        }
        return res;
      });
    })
  );
});
