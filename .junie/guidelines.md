# Project Guidelines

* Antwort bitte maximal 3 Sätze, keine Nachfragen.
* Kein Plan, keine Status‑Updates, nur direkte Antwort, außer es wird nach einem Plan gefragt.
* Nichts ausführen/keine Tools, nur [CHAT]-Antwort.
* Keine Code‑Änderungen ohne meine explizite Freigabe.
* Vor jeder längeren Antwort erst Rückfrage stellen.

## Projektüberblick (kurz)
- chrani_bot_tng ist ein modularer Python‑Bot mit Web‑UI (LCARS‑Stil) und Telnet‑Anbindung, u. a. für Server‑/Spielumgebungen.
- Einstiegspunkte: `app.py` (lokal) und `wsgi.py` (WSGI/Gunicorn); Module unter `bot/modules/*` (z. B. telnet, webserver, players, locations, permissions).
- HTML/Jinja2‑Templates und Widgets liegen in den jeweiligen Modul‑Ordnern; statische Assets unter `bot/modules/webserver/static`.
- Deployment/Service‑Hinweise: `bot/resources/DEPLOYMENT.md`, `bot/resources/chrani-bot-tng.service`, `bot/resources/gunicorn.conf.py`, `bot/resources/nginx.conf.example`.
 