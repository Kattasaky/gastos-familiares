const CACHE_NAME = 'gastos-familiares-v1';
const URLS_A_CACHEAR = [
    '/',
    '/gastos/',
    '/compras/',
    '/ingresos/',
    '/recurrentes/',
    '/metas/',
    '/prestamos/',
    '/alertas/',
    '/static/manifest.json',
];

// Al instalar, guarda en caché las páginas principales
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(URLS_A_CACHEAR);
        })
    );
    self.skipWaiting();
});

// Al activar, elimina cachés viejos
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            );
        })
    );
    self.clients.claim();
});

// Al hacer fetch: intenta la red, si falla usa caché
self.addEventListener('fetch', event => {
    // Solo cachear peticiones GET
    if (event.request.method !== 'GET') return;

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Si la respuesta es válida, guardarla en caché
                if (response && response.status === 200) {
                    const copia = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, copia);
                    });
                }
                return response;
            })
            .catch(() => {
                // Sin internet, buscar en caché
                return caches.match(event.request).then(cached => {
                    if (cached) return cached;
                    // Si no está en caché, mostrar página de inicio
                    return caches.match('/');
                });
            })
    );
});
