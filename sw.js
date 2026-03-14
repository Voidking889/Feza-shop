const CACHE_NAME = 'feza-shop-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/seller_dashboard.html',
    '/live_delivery.html',
    '/login_signup.html',
    '/feza_shop_presentation.html',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap'
];

// Install Event: Cache Core Assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .catch(err => console.error('Service Worker Install Error:', err))
    );
});

// Activate Event: Clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch Event: Network-first, fallback to cache
self.addEventListener('fetch', event => {
    // Skip cross-origin requests like APIs
    if (!event.request.url.startsWith(self.location.origin) && !ASSETS_TO_CACHE.includes(event.request.url)) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // If network fetch is successful and valid, update cache
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }
                const responseToCache = response.clone();
                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(event.request, responseToCache);
                    });
                return response;
            })
            .catch(() => {
                // If offline, serve from cache
                return caches.match(event.request);
            })
    );
});
