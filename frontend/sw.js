const SHELL_CACHE = 'maize-shell-v4';
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

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isSensitiveRequest(url)) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('./offline.html'))
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then(response => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then(cache => cache.put(request, copy));
        }
        return response;
      })
      .catch(() => caches.match(request))
  );
});
