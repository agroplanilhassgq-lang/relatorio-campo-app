const CACHE_NAME = 'relatorio-campo-v1';

const ASSETS = [
  '/',
  '/static/style.css',
  '/static/logo.png',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS.filter(url => url !== '/static/logo.png'));
    }).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Cache-first para arquivos estáticos
  if (url.pathname.startsWith('/static/') && !url.pathname.startsWith('/static/uploads/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        return cached || fetch(event.request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        }).catch(() => cached);
      })
    );
    return;
  }

  // Network-first para navegação (páginas HTML)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match('/').then(cached => {
          if (cached) return cached;
          return new Response(
            `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sem conexão</title>
            <style>
              body { font-family: Arial, sans-serif; display: flex; align-items: center;
                justify-content: center; min-height: 100vh; margin: 0; background: #eef2f5; }
              .box { text-align: center; background: white; padding: 40px; border-radius: 16px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 400px; }
              h1 { color: #0f172a; margin-bottom: 12px; }
              p { color: #64748b; margin-bottom: 20px; }
              button { background: #1d4ed8; color: white; border: none; padding: 12px 24px;
                border-radius: 10px; font-size: 15px; cursor: pointer; }
            </style></head>
            <body><div class="box">
              <h1>Sem conexão</h1>
              <p>Você está offline. Os dados do formulário são salvos automaticamente no dispositivo.</p>
              <button onclick="window.history.back()">Voltar</button>
            </div></body></html>`,
            { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
          );
        });
      })
    );
    return;
  }
});
