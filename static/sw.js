const CACHE_NAME = 'weather-shell-v1';
const RUNTIME_CACHE = 'weather-runtime-v1';

const PRECACHE_URLS = [
  '/',
  '/static/styles.css',
  '/static/js/weather.js',
  '/static/manifest.webmanifest',
  '/static/offline.html',
  '/static/icons/icon-180.png',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => ![CACHE_NAME, RUNTIME_CACHE].includes(key))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

function stashResponse(request, response) {
  if (!response) return;
  if (!response.ok && response.type !== 'opaque') return;
  caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, response.clone()));
}

function networkFirst(request) {
  return fetch(request)
    .then((response) => {
      stashResponse(request, response);
      return response;
    })
    .catch(() =>
      caches.match(request, { ignoreSearch: true }).then((cached) => {
        if (cached) return cached;
        return caches.match('/static/offline.html');
      })
    );
}

function staleWhileRevalidate(request) {
  return caches.match(request).then((cached) => {
    const fetchPromise = fetch(request)
      .then((response) => {
        stashResponse(request, response);
        return response;
      })
      .catch(() => cached);
    return cached || fetchPromise;
  });
}

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') {
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(networkFirst(event.request));
    return;
  }

  const requestUrl = new URL(event.request.url);

  if (requestUrl.origin === self.location.origin) {
    event.respondWith(staleWhileRevalidate(event.request));
    return;
  }

  event.respondWith(staleWhileRevalidate(event.request));
});
