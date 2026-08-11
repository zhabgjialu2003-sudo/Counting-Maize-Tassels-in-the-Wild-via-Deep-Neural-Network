const SHELL_CACHE = 'maize-shell-v10';
const SHELL_ASSETS = [
  './offline.html',
  './pages/login.html',
  './pages/mobile.html',
  './pages/profile.html',
  './pages/upload.html',
  './pages/leaf.html',
  './pages/result.html',
  './pages/history.html',
  './css/style.css',
  './css/mobile.css',
  './js/api.js',
  './js/auth.js',
  './js/mobile.js',
  './js/leaf.js',
  './js/dashboard.js',
  './js/pwa.js',
  './icons/maize-icon-192.png',
  './icons/maize-icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.addAll(SHELL_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== SHELL_CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

function isSensitiveRequest(url) {
  return url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/uploads/') ||
    url.pathname.startsWith('/storage/');
}

async function offlineNavigationResponse() {
  const offlineUrl = new URL('./offline.html', self.location.href).href;
  return (await caches.match(offlineUrl)) || new Response(
    '<!doctype html><html lang="en"><meta charset="utf-8"><title>Offline</title>' +
    '<body><h1>You are offline</h1><p>Reconnect and try again.</p></body></html>',
    {
      status: 503,
      statusText: 'Offline',
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    },
  );
}

async function cachedAssetOrError(request) {
  return (await caches.match(request)) || new Response('', {
    status: 504,
    statusText: 'Offline asset unavailable',
  });
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isSensitiveRequest(url)) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          return await fetch(request);
        } catch (error) {
          return offlineNavigationResponse();
        }
      })()
    );
    return;
  }

  event.respondWith(
    (async () => {
      try {
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(SHELL_CACHE);
          await cache.put(request, response.clone());
        }
        return response;
      } catch (error) {
        return cachedAssetOrError(request);
      }
    })()
  );
});
