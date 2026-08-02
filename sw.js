// Service Worker —— 让 PWA 可离线、可“添加到主屏幕”
const CACHE = 'diet-tracker-v3';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192-v2.png',
  './icon-512-v2.png',
  './apple-touch-icon-v2.png'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS)).catch(() => {})
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  const isHtml = url.pathname.endsWith('.html') || url.pathname === '/' || url.pathname.endsWith('/');
  if (isHtml) {
    // HTML 页面始终走网络，并强制向源服务器重新拉取（cache:reload），
    // 完全绕过浏览器 HTTP 缓存，保证重新部署后手机端立即看到更新
    event.respondWith(
      fetch(event.request, { cache: 'reload' }).catch(() => caches.match('./index.html'))
    );
    return;
  }
  event.respondWith(
    fetch(event.request)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(cache => cache.put(event.request, copy));
        return res;
      })
      .catch(() => caches.match(event.request).then(r => r || caches.match('./index.html')))
  );
});
