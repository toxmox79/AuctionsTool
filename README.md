# eBay Auction SEO Tool

Installierbare PWA zur Erstellung und Aufbereitung von eBay-Listings, Artikelmerkmalen und Produktbildern.

## GitHub Pages

Nach dem Push auf `main` oder `master` veröffentlicht der Workflow die PWA automatisch. Im Repository muss unter **Settings → Pages → Build and deployment** die Quelle **GitHub Actions** ausgewählt sein.

Die veröffentlichte PWA enthält die 17 mitgelieferten JSON-Standardkategorien und funktioniert nach dem ersten vollständigen Laden auch offline.

## Live-Suche in der installierten PWA

Die eBay-Live-Suche benötigt entweder den lokalen Python-Dienst (`Start.bat`, läuft auf `http://127.0.0.1:8765`) oder einen öffentlich erreichbaren CORS-Proxy (z. B. Cloudflare Worker, Datei `proxy-worker.js`), weil die eBay-API keine CORS-Header sendet und das Client Secret nicht im Browser liegen darf.

Der lokale Dienst startet mit `Start.bat`. Für den Proxy-Modus die Worker-URL in den PWA-Einstellungen unter „API-Proxy“ eintragen. Das Client Secret bleibt dabei geschützt und wird nicht an den Browser ausgeliefert.

Weitere Hinweise stehen in [PWA-GITHUB.md](PWA-GITHUB.md).
