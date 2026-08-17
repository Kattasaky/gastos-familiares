const CACHE_NAME = 'gastos-familiares-v2';

// Solo se cachean archivos que NUNCA cambian con las acciones del usuario.
// Las páginas con datos financieros (gastos, recurrentes, ingresos, etc.)
// se excluyen a propósito: deben pedirse siempre a la red para evitar
// mostrar estados de pago desactualizados.
const URLS_A_CACHEAR = [
    '/static/manifest.json',
];

// Rutas que NUNCA deben servirse desde caché, aunque la red falle o tarde.
const RUTAS_SIEMPRE_RED = [
    '/',
    '/gastos/',
    '/compras/',
    '/ingresos/',
    '/recurrentes/',
    '/metas/',
    '/prestamos/',
    '/alertas/',
];

function esRutaDinamica(url) {
    const path = new URL(url).pathname;
    return RUTAS_SIEMPRE_RED.some(ruta => path === ruta || path.startsWith(ruta));
}

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(URLS_A_CACHEAR);
        })
    );
    self.skipWaiting();
});

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

self.addEventListener('fetch', event => {
    // Solo interceptar peticiones GET; POST (pagar, eliminar, etc.) siempre va directo a la red.
    if (event.request.method !== 'GET') return;

    // Páginas con datos financieros: SIEMPRE red, sin fallback a caché.
    // Si el servidor está lento (Render "despertando"), el navegador espera
    // la respuesta real en vez de mostrar una versión vieja guardada.
    if (esRutaDinamica(event.request.url)) {
        event.respondWith(fetch(event.request));
        return;
    }

    // Archivos estáticos (CSS, JS, íconos, manifest): red primero, caché como respaldo offline.
    event.respondWith(
        fetch(event.request)
            .then(response => {
                if (response && response.status === 200) {
                    const copia = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, copia);
                    });
                }
                return response;
            })
            .catch(() => {
                return caches.match(event.request);
            })
    );
});
