# Veröffentlichung als PWA über GitHub Pages

## So funktioniert die Live-Suche in der installierten PWA

Die eBay-API sendet keine CORS-Header. Ein direkter Aufruf aus dem Browser ist deshalb technisch unmöglich, und das Client Secret darf ohnehin nicht im Browser liegen. Der lokale Python-Dienst löst beides: Er spricht mit eBay, hält das Secret lokal und gibt nur die fertigen Ergebnisse an den Browser weiter.

Damit die **von GitHub Pages installierte PWA** den lokalen Dienst erreicht, läuft der Dienst auf der festen Adresse `http://127.0.0.1:8765`. Browser behandeln Loopback-Adressen als sicheren Kontext, deshalb wird der Aufruf von einer HTTPS-Seite aus nicht blockiert.

Die PWA ermittelt beim Start selbst, wo der Dienst liegt:

1. Läuft die Seite selbst über den lokalen Dienst, wird die eigene Herkunft verwendet.
2. Andernfalls wird die Adresse aus **Einstellungen → Lokaler eBay-Dienst** verwendet, Standard ist `http://127.0.0.1:8765`.

Der Dienst läuft nur auf `127.0.0.1` und ist damit ausschließlich vom eigenen Rechner erreichbar. Die Zugangsdaten liegen im lokalen `data`-Ordner des Explorers und werden nicht an den Browser ausgeliefert.

## Lokal mit eBay-Live-Suche

`Start.bat` starten. Der lokale Python-Dienst öffnet das Auktionstool und stellt die geschützten API-Endpunkte für den integrierten eBay Category Explorer bereit. Die Zugangsdaten werden im lokalen `data`-Ordner des Explorers gespeichert und nicht an den Browser ausgeliefert.

Wird `Start.bat` ein zweites Mal gestartet, erkennt der Dienst den laufenden Dienst, öffnet ihn im Browser und beendet sich.

Die 17 JSON-Kategorien sind immer als Standardauswahl verfügbar. Weitere über eBay geladene Kategorien werden im lokalen Cache gespeichert und beim nächsten Start unter **Weitere eBay-Kategorien** wieder angeboten.

## GitHub Pages

1. Alle Dateien dieses Ordners in ein GitHub-Repository hochladen.
2. Unter **Settings → Pages → Build and deployment** als Quelle **GitHub Actions** auswählen.
3. Den Branch `main` oder `master` pushen. Der Workflow veröffentlicht die App automatisch.
4. Die ausgegebene Pages-Adresse in Chrome oder Edge öffnen und über das Installationssymbol als App installieren.

Der Service Worker funktioniert nur über HTTPS beziehungsweise `localhost`, nicht beim direkten Öffnen als `file://`-Datei.

Auf GitHub Pages sind die JSON-Standardkategorien offline verfügbar. Für die Live-Suche muss zusätzlich `Start.bat` auf demselben Rechner laufen; die installierte PWA findet den Dienst dann automatisch.
