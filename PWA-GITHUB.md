# Veröffentlichung als PWA über GitHub Pages

1. Alle Dateien dieses Ordners in ein GitHub-Repository hochladen.
2. Unter **Settings → Pages → Build and deployment** als Quelle **GitHub Actions** auswählen.
3. Den Branch `main` oder `master` pushen. Der Workflow veröffentlicht die App automatisch.
4. Die ausgegebene Pages-Adresse in Chrome oder Edge öffnen und über das Installationssymbol als App installieren.

Der Service Worker funktioniert nur über HTTPS beziehungsweise `localhost`, nicht beim direkten Öffnen als `file://`-Datei.
