# Project Guidelines

* Keine übrerlangen Status‑Updates.
* Keine Code‑Änderungen ohne meine explizite Freigabe.
* Vor jeder längeren Antwort erst Rückfrage stellen.
* Read-only Terminal Befehle darfst du immer ungefragt ausführen.
* Jeden Plan bestätigen lassen.
* Keine Zeitschätzungen.

## Projektüberblick (kurz)
Folgende Dateien und Ordner gehören NICHT zum Projekt und werden niemals durchsucht: 
```
/venv/*
```

Folgende Datein und Ordner sind für dich read-only. Da wird nichts bearbeitet, gelöscht oder anderweitig verändert, es sei denn, ich bitte dich darum die dokumentation anzupassen.
```
/bot/resources/*
```

- chrani_bot_tng ist ein modularer Python‑Bot mit Web‑UI (LCARS‑Stil) und Telnet‑Anbindung, u. a. für Server‑/Spielumgebungen.
- Einstiegspunkte: `app.py` (lokal) und `wsgi.py` (WSGI/Gunicorn); Module unter `bot/modules/*` (z. B. telnet, webserver, players, locations, permissions).
- HTML/Jinja2‑Templates und Widgets liegen in den jeweiligen Modul‑Ordnern; statische Assets unter `bot/modules/webserver/static`.
- Informational Resources in `bot/resources/*.md`.
 