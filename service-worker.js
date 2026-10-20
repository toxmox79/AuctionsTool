const CACHE_NAME = 'ebay-auction-tool-v10';
const APP_SHELL = [
  './',
  './index.html',
  './ebay-auction-tool.html',
  './manifest.webmanifest',
  './Icon.png',
  './Icon-192.png',
  './Icon-512.png',
  './Icon-maskable-192.png',
  './Icon-maskable-512.png',
  './Einbaugerät.png',
  './Möbelfront.png',
  './Einbaugeraet-overlay.png',
  './Moebelfront-overlay.png',
  './categories/index.json',
  './categories/Backofen_71318.json',
  './categories/Bügeleisen_43513.json',
  './categories/Dunstabzugshauben_71253.json',
  './categories/Gefriergeräte_71260.json',
  './categories/Heizgeräte_20613.json',
  './categories/Herd_71250.json',
  './categories/Kochfeld_71246.json',
  './categories/Kombinationsgeräte_20713.json',
  './categories/Kühlschrank_71262.json',
  './categories/Lampen_112581.json',
  './categories/Mikrowelle_150140.json',
  './categories/Staubsauger_20614.json',
  './categories/Trockner_71254.json',
  './categories/TV&Fernseher_11071.json',
  './categories/Waschmaschinen_71256.json',
  './categories/Waschtrockner_71257.json',
  './categories/Weinkühlschrank_177750.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);
  if (requestUrl.origin !== self.location.origin) return;

  // API-Anfragen nie abfangen – immer direkt durchreichen.
  if (requestUrl.pathname.startsWith('/api/')) return;

  // Kategorieexporte werden bei jedem Start bevorzugt frisch geladen, damit
  // ausgetauschte JSON-Dateien ohne weiteren Codewechsel wirksam werden.
  if (requestUrl.pathname.includes('/categories/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(event.request);
          if (cached) return cached;
          // Fallback auf index.json falls einzelne Datei fehlt
          if (requestUrl.pathname.includes('index.json')) {
            const indexCached = await caches.match('./categories/index.json');
            if (indexCached) return indexCached;
          }
          throw new Error('Kategorie-Daten nicht verfügbar');
        })
    );
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          return response;
        })
        .catch(async () =>
          (await caches.match(event.request)) || caches.match('./ebay-auction-tool.html')
        )
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      }
      return response;
    }))
  );
});
