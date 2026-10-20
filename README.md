# eBay Auction SEO Tool

Installierbare PWA zur Erstellung und Aufbereitung von eBay-Listings, Artikelmerkmalen und Produktbildern.

## GitHub Pages

Nach dem Push auf `main` oder `master` veröffentlicht der Workflow die PWA automatisch. Im Repository muss unter **Settings → Pages → Build and deployment** die Quelle **GitHub Actions** ausgewählt sein.

Die veröffentlichte PWA enthält die 17 mitgelieferten JSON-Standardkategorien und funktioniert nach dem ersten vollständigen Laden auch offline.

## Live-Suche in der installierten PWA

Die eBay-Live-Suche benötigt den lokalen Python-Dienst, weil die eBay-API kein CORS erlaubt und das Client Secret nicht im Browser liegen darf. `Start.bat` startet den Dienst auf `http://127.0.0.1:8765`.

Die installierte PWA verbindet sich automatisch mit diesem Dienst, auch wenn sie von GitHub Pages geladen wurde. Einmal `Start.bat` starten genügt; die PWA merkt sich die Adresse.

Weitere Hinweise stehen in [PWA-GITHUB.md](PWA-GITHUB.md).
