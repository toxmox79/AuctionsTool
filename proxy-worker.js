// eBay API Proxy (Cloudflare Workers)
// Stellt CORS-Header bereit und leitet eBay-Aufrufe weiter.
// Es werden KEINE Zugangsdaten dauerhaft gespeichert – diese werden pro
// Anfrage mitgesendet. Damit funktioniert die PWA auch auf statischem
// Hosting (z. B. GitHub Pages) ohne eigenen Server.
//
// Deployment:
//   1. wrangler init (oder Cloudflare Dashboard → Workers → Create)
//   2. Diese Datei als Worker-Skript hinterlegen
//   3. Worker-Route bereitstellen, z. B. https://ebay-proxy.<user>.workers.dev
//   4. Die Worker-URL in den Einstellungen der PWA unter "API-Proxy" eintragen

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Ebay-Client-Id, X-Ebay-Client-Secret',
  'Access-Control-Max-Age': '86400',
  'Vary': 'Origin',
};

async function readJson(request) {
  try {
    return await request.json();
  } catch (e) {
    return {};
  }
}

function basicAuth(clientId, clientSecret) {
  return 'Basic ' + btoa(unescape(encodeURIComponent(clientId)) + ':' + unescape(encodeURIComponent(clientSecret)));
}

async function fetchToken(clientId, clientSecret, environment) {
  const domain = environment === 'sandbox' ? 'api.sandbox.ebay.com' : 'api.ebay.com';
  const resp = await fetch(`https://${domain}/identity/v1/oauth2/token`, {
    method: 'POST',
    headers: {
      'Authorization': basicAuth(clientId, clientSecret),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: 'grant_type=client_credentials&scope=https://api.ebay.com/oauth/api_scope',
  });
  const body = await resp.text();
  return { status: resp.status, body };
}

async function jsonResponse(data, status, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS, 'Content-Type': 'application/json; charset=utf-8', ...extraHeaders },
  });
}

async function proxyResponse(response) {
  const ct = response.headers.get('content-type') || 'application/json';
  const data = await response.text();
  return new Response(data, {
    status: response.status,
    headers: { ...CORS, 'Content-Type': ct },
  });
}

async function handleRequest(request) {
  const url = new URL(request.url);

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: CORS });
  }

  // Health-Check
  if (url.pathname === '/' || url.pathname === '/api/health') {
    return new Response('ok', { headers: { ...CORS, 'Content-Type': 'text/plain' } });
  }

  // --- Token holen (Client-Credentials Flow) ---
  if (url.pathname === '/api/token' && request.method === 'POST') {
    const { client_id, client_secret, environment = 'production' } = await readJson(request);
    if (!client_id || !client_secret) {
      return jsonResponse({ error: 'client_id und client_secret erforderlich' }, 400);
    }
    try {
      const result = await fetchToken(client_id, client_secret, environment);
      return new Response(result.body, { status: result.status, headers: { ...CORS, 'Content-Type': 'application/json; charset=utf-8' } });
    } catch (err) {
      return jsonResponse({ error: 'Token-Anfrage fehlgeschlagen', detail: String(err) }, 502);
    }
  }

  // --- Generischer eBay-Proxy (Authorization: Bearer Header vorausgesetzt) ---
  if (url.pathname === '/api/proxy' && request.method === 'POST') {
    const { method = 'GET', path, headers = {}, body } = await readJson(request);
    if (!path || typeof path !== 'string') {
      return jsonResponse({ error: 'path erforderlich' }, 400);
    }
    const fwdHeaders = {};
    for (const [key, value] of Object.entries(headers)) {
      if (key.toLowerCase() !== 'host' && key.toLowerCase() !== 'content-length') {
        fwdHeaders[key] = value;
      }
    }
    try {
      const response = await fetch('https://api.ebay.com' + path, {
        method,
        headers: fwdHeaders,
        body: method === 'GET' || method === 'HEAD' ? undefined : (body || undefined),
      });
      return await proxyResponse(response);
    } catch (err) {
      return jsonResponse({ error: 'Proxy-Anfrage fehlgeschlagen', detail: String(err) }, 502);
    }
  }

  return jsonResponse({ error: 'not found' }, 404);
}
