const SW_VERSION = new URL(self.location.href).searchParams.get('v') || 'v1';
const CACHE_NAME = `weather-shell-${SW_VERSION}`;
const RUNTIME_CACHE = `weather-runtime-${SW_VERSION}`;
const NAVIGATION_TIMEOUT_MS = 3000;

const PRECACHE_URLS = [
  '/',
  '/static/styles.css',
  '/static/js/weather.js',
  '/manifest.webmanifest',
  '/static/offline.html',
  '/static/icons/icon-180.png',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

const VERSIONED_URLS = new Set([
  '/',
  '/static/styles.css',
  '/static/js/weather.js',
  '/manifest.webmanifest',
  '/static/offline.html',
]);

const PRECACHE_REQUESTS = PRECACHE_URLS.map((url) => {
  if (!VERSIONED_URLS.has(url)) {
    return url;
  }
  if (url.includes('?')) {
    return `${url}&v=${SW_VERSION}`;
  }
  return `${url}?v=${SW_VERSION}`;
});

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_REQUESTS))
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
  if (response.bodyUsed) return;
  const responseClone = response.clone();
  caches
    .open(RUNTIME_CACHE)
    .then((cache) => cache.put(request, responseClone))
      .catch(() => {});
}

function matchNavigationCache(request) {
  try {
    const requestUrl = new URL(request.url);
    if (requestUrl.origin === self.location.origin && requestUrl.pathname === '/' && !requestUrl.search) {
      return caches.match(request, { ignoreSearch: true });
    }
  } catch (error) {
    // Fall back to default cache lookup.
  }
  return caches.match(request);
}

function networkFirst(request, { timeoutMs = 0, cacheMatch } = {}) {
  const cacheLookup = cacheMatch || ((req) => caches.match(req, { ignoreSearch: true }));
  const fetchPromise = fetch(request).then((response) => {
    stashResponse(request, response);
    return response;
  });

  if (!timeoutMs) {
    return fetchPromise.catch(() =>
      cacheLookup(request).then((cached) => {
        if (cached) return cached;
        return caches.match('/static/offline.html', { ignoreSearch: true });
      })
    );
  }

  return new Promise((resolve) => {
    let settled = false;

    const finalize = (response) => {
      if (settled || !response) return;
      settled = true;
      resolve(response);
    };

    const timeoutId = setTimeout(() => {
      cacheLookup(request).then((cached) => {
        finalize(cached);
      });
    }, timeoutMs);

    fetchPromise
      .then((response) => {
        clearTimeout(timeoutId);
        finalize(response);
      })
      .catch(() => {
        clearTimeout(timeoutId);
        cacheLookup(request).then((cached) => {
          if (cached) return finalize(cached);
          return caches.match('/static/offline.html', { ignoreSearch: true }).then(finalize);
        });
      });
  });
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
    event.respondWith(
      networkFirst(event.request, {
        timeoutMs: NAVIGATION_TIMEOUT_MS,
        cacheMatch: matchNavigationCache,
      })
    );
    return;
  }

  const requestUrl = new URL(event.request.url);

  if (requestUrl.origin === self.location.origin) {
    event.respondWith(staleWhileRevalidate(event.request));
    return;
  }

  event.respondWith(staleWhileRevalidate(event.request));
});
