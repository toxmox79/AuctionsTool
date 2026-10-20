# Veröffentlichung als PWA über GitHub Pages

## Wichtiger Hinweis zur eBay-Live-Suche

Die eBay-API sendet **keine CORS-Header**. Ein direkter Aufruf aus dem Browser ist deshalb technisch unmöglich, und das Client Secret darf aus Sicherheitsgründen nicht im Browser (Quelltext / localStorage einer öffentlichen Seite) liegen.

Die PWA unterstützt deshalb zwei Betriebsarten für die Live-Suche:

| Modus | Voraussetzung | Zugangsdaten |
|-------|---------------|----------------|
| **Lokaler Dienst** (`Start.bat`) | Python-Dienst läuft auf dem eigenen Rechner | Werden im lokalen `data`-Ordner gespeichert |
| **API-Proxy** (Cloudflare Worker etc.) | Öffentlich erreichbarer Proxy mit CORS | Werden clientseitig im Browser gespeichert |

Ohne einen der beiden Modi stehen nur die 17 mitgelieferten JSON-Standardkategorien (offline) zur Verfügung.

---

## Variante A: Lokaler Dienst (Start.bat) — empfohlen für den eigenen Rechner

`Start.bat` starten. Der lokale Python-Dienst öffnet das Auktionstool und stellt die geschützten API-Endpunkte bereit. Er läuft auf der festen Adresse `http://127.0.0.1:8765` (Browser behandeln Loopback-Adressen als sicheren Kontext, deshalb wird der Aufruf von einer HTTPS-PWA-Seite aus nicht blockiert).

Die installierte PWA ermittelt beim Start selbst, wo der Dienst liegt:

1. Läuft die Seite selbst über den lokalen Dienst, wird die eigene Herkunft verwendet.
2. Andernfalls wird die Adresse aus **Einstellungen → Lokaler eBay-Dienst** verwendet, Standard ist `http://127.0.0.1:8765`.

Wird `Start.bat` ein zweites Mal gestartet, erkennt der Dienst den laufenden Dienst, öffnet ihn im Browser und beendet sich.

Die Zugangsdaten liegen im lokalen `data`-Ordner des Explorers und werden nicht an den Browser ausgeliefert.

---

## Variante B: API-Proxy — PWA direkt ohne Start.bat (z. B. auf GitHub Pages)

Damit die von GitHub Pages installierte PWA die eBay-Live-Suche nutzt, ohne dass ein lokaler Dienst laufen muss, stellt ein kleiner CORS-Proxy (z. B. ein Cloudflare Worker) die Verbindung zu eBay her. Der Proxy speichert **keine** Zugangsdaten dauerhaft; diese werden pro Anfrage mitgesendet.

### Proxy bereitstellen (`proxy-worker.js`)

1. Cloudflare Worker erstellen (Dashboard → Workers & Pages → Create a Service, oder `wrangler init`).
2. Die Datei `proxy-worker.js` aus diesem Repository als Worker-Skript hinterlegen.
3. Den Worker bereitstellen, z. B. `https://ebay-proxy.<deinname>.workers.dev`.

### PWA konfigurieren

1. Die installierte PWA öffnen → **Einstellungen**.
2. Unter **API-Proxy** die Worker-URL eintragen, z. B. `https://ebay-proxy.deinname.workers.dev`.
3. Client ID und Client Secret (Cert ID) eingeben und **Einstellungen speichern**.
4. **Verbindung testen** – der Proxy holt ein echtes eBay-Access-Token.

Die Zugangsdaten werden dann clientseitig im Browser gespeichert (localStorage) und nur an den eigenen Proxy gesendet, nie an eBay direkt aus dem Browser.

---

## Zugangsdaten bei eBay

Die Live-Suche funktioniert nur mit gültigen eBay-Entwicklerzugangsdaten (App ID / Client ID + Cert ID / Client Secret für die Umgebung „Production“). Diese erhält man im [eBay Developer Portal](https://developer.ebay.com/). Liefert eBay `invalid_client`, sind die Zugangsdaten falsch oder das Konto/de App nicht für die gewählte Umgebung freigeschaltet.

---

## GitHub Pages (Veröffentlichung)

1. Alle Dateien dieses Ordners (inkl. `proxy-worker.js`) in ein GitHub-Repository hochladen.
2. Unter **Settings → Pages → Build and deployment** als Quelle **GitHub Actions** auswählen.
3. Den Branch `main` oder `master` pushen. Der Workflow veröffentlicht die App automatisch.
4. Die ausgegebene Pages-Adresse in Chrome oder Edge öffnen und über das Installationssymbol als App installieren.

Der Service Worker funktioniert nur über HTTPS beziehungsweise `localhost`, nicht beim direkten Öffnen als `file://`-Datei.

Auf GitHub Pages sind die JSON-Standardkategorien immer offline verfügbar. Für die eBay-Live-Suche ist entweder der lokale Dienst (`Start.bat`) oder ein konfigurierter API-Proxy erforderlich.
