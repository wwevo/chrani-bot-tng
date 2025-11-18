# chrani-bot-tng Deployment-Anleitung

Umfassende Anleitung zur Installation, Konfiguration und zum Betrieb von chrani-bot-tng mit modernem Python, gunicorn und nginx.

## Inhaltsverzeichnis

1. [Systemanforderungen](#systemanforderungen)
2. [Schnellstart - Lokales Testen](#schnellstart---lokales-testen)
3. [Produktions-Deployment mit gunicorn](#produktions-deployment-mit-gunicorn)
4. [Deployment mit nginx (Reverse Proxy)](#deployment-mit-nginx-reverse-proxy)
5. [Systemd-Service einrichten](#systemd-service-einrichten)
6. [Fehlerbehebung](#fehlerbehebung)
7. [Wartung und Updates](#wartung-und-updates)

---

## Systemanforderungen

### Unterstützte Systeme
- **Linux**: Ubuntu 20.04+, Debian 10+, CentOS 8+, Fedora, Arch Linux
- **Python**: 3.8 oder höher (empfohlen: Python 3.10+)
- **Weitere Software**:
  - Git
  - pip (Python Package Manager)
  - virtualenv oder venv
  - Optional: nginx (für Reverse Proxy)
  - Optional: systemd (für Service-Management)

### Mindestanforderungen Hardware
- **CPU**: 1 Core
- **RAM**: 512 MB (1 GB empfohlen)
- **Festplatte**: 500 MB freier Speicher

---

## Schnellstart - Lokales Testen

Diese Anleitung zeigt Ihnen, wie Sie chrani-bot-tng lokal auf Ihrem Computer zum Testen ausführen können.

### Schritt 1: Repository klonen

```bash
cd ~
git clone https://github.com/your-username/chrani-bot-tng.git
cd chrani-bot-tng
```

### Schritt 2: Python Virtual Environment erstellen

Ein Virtual Environment isoliert die Python-Abhängigkeiten des Projekts von Ihrem System.

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Virtual Environment aktivieren
source venv/bin/activate

# Ihr Prompt sollte jetzt mit (venv) beginnen
```

### Schritt 3: Abhängigkeiten installieren

```bash
# pip aktualisieren
pip install --upgrade pip

# Projektabhängigkeiten installieren
pip install -r requirements.txt
```

### Schritt 4: Konfiguration anpassen

Die Bot-Konfiguration befindet sich in JSON-Dateien im `bot/options/` Verzeichnis.

```bash
# Verzeichnis prüfen
ls -la bot/options/

# Beispiel: Webserver-Konfiguration bearbeiten
nano bot/options/module_webserver.json
```

**Wichtige Einstellungen** in `module_webserver.json`:
```json
{
  "host": "0.0.0.0",
  "port": 5000,
  "Flask_secret_key": "ÄNDERN-SIE-DIES-IN-PRODUKTION"
}
```

**Telnet-Konfiguration** (für Verbindung zum 7 Days to Die Server):
```bash
nano bot/options/module_telnet.json
```

Passen Sie die Telnet-Verbindungsdetails an Ihren Gameserver an.

### Schritt 5: Bot starten (Entwicklungsmodus)

Es gibt zwei Möglichkeiten, den Bot zu starten:

#### Methode A: Standalone-Modus (Flask Development Server)

```bash
# Mit dem originalen Entry-Point
python3 app.py
```

Der Bot sollte starten und ausgeben:
```
modules started: ['module_dom', 'module_storage', 'module_telnet', ...]
```

Der Webserver läuft auf: `http://localhost:5000`

#### Methode B: Mit gunicorn (empfohlen für Tests)

```bash
# Mit gunicorn starten (wie in Produktion)
gunicorn -c gunicorn.conf.py wsgi:application
```

Vorteile:
- Näher an der Produktionsumgebung
- Bessere Performance
- WebSocket-Support optimiert

### Schritt 6: Im Browser testen

Öffnen Sie Ihren Browser und navigieren Sie zu:

```
http://localhost:5000
```

Sie sollten die LCARS-Style Weboberfläche sehen. Klicken Sie auf "use your steam-account to log in" um sich zu authentifizieren.

### Schritt 7: Bot beenden

```bash
# STRG+C drücken um den Bot zu stoppen

# Virtual Environment deaktivieren
deactivate
```

---

## Produktions-Deployment mit gunicorn

Für den Produktionsbetrieb ist gunicorn deutlich besser geeignet als der Flask Development Server.

### Warum gunicorn?

- **Performance**: Optimiert für hohe Last und viele gleichzeitige Verbindungen
- **Stabilität**: Automatisches Neustart bei Fehlern
- **WebSocket-Support**: Mit gevent-Worker für Socket.IO optimiert
- **Production-Ready**: Bewährt in vielen großen Projekten

### Schritt 1: Konfiguration überprüfen

Die Datei `gunicorn.conf.py` enthält die gunicorn-Konfiguration:

```bash
nano gunicorn.conf.py
```

**Wichtige Einstellungen**:

```python
# Server Socket - wo gunicorn lauscht
bind = "0.0.0.0:5000"  # Alle Interfaces, Port 5000

# Worker - WICHTIG: Für WebSocket nur 1 Worker!
workers = 1
worker_class = "gevent"  # Für Socket.IO erforderlich
worker_connections = 1000

# Timeouts
timeout = 120
keepalive = 5
```

### Schritt 2: Bot mit gunicorn starten

```bash
# Virtual Environment aktivieren
cd ~/chrani-bot-tng
source venv/bin/activate

# Mit gunicorn starten
gunicorn -c gunicorn.conf.py wsgi:application
```

Sie sollten folgende Ausgabe sehen:

```
============================================================
chrani-bot-tng is starting...
============================================================
Worker spawned (pid: 12345)
Worker initialized (pid: 12345)
webserver: Running under WSGI server mode
modules started: [...]
============================================================
chrani-bot-tng is ready to accept connections
Listening on: 0.0.0.0:5000
============================================================
```

### Schritt 3: Verbindung testen

```bash
# In einem neuen Terminal:
curl http://localhost:5000

# Oder im Browser:
# http://your-server-ip:5000
```

### Schritt 4: Bot im Hintergrund laufen lassen

```bash
# Mit nohup (einfache Methode)
nohup gunicorn -c gunicorn.conf.py wsgi:application > gunicorn.log 2>&1 &

# Prozess-ID wird angezeigt
echo $! > gunicorn.pid

# Logs anschauen
tail -f gunicorn.log

# Bot stoppen
kill $(cat gunicorn.pid)
```

**Besser**: Verwenden Sie systemd (siehe Abschnitt unten)

---

## Deployment mit nginx (Reverse Proxy)

nginx als Reverse Proxy bietet zusätzliche Vorteile:

- **SSL/TLS-Terminierung** (HTTPS-Verschlüsselung)
- **Load Balancing** (bei mehreren Instanzen)
- **Static File Serving** (schnelleres Ausliefern von CSS/JS)
- **DDoS-Schutz** und Rate Limiting
- **Besseres Logging**

### Schritt 1: nginx installieren

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx

# Fedora
sudo dnf install nginx
```

### Schritt 2: nginx-Konfiguration erstellen

```bash
# Beispielkonfiguration kopieren
sudo cp nginx.conf.example /etc/nginx/sites-available/chrani-bot-tng

# Konfiguration bearbeiten
sudo nano /etc/nginx/sites-available/chrani-bot-tng
```

**Wichtige Anpassungen**:

1. **Server-Name ändern**:
```nginx
server_name your-domain.com www.your-domain.com;
```

2. **SSL-Zertifikate** (für HTTPS):
```nginx
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

3. **Upstream-Server prüfen**:
```nginx
upstream chrani_bot_app {
    server 127.0.0.1:5000 fail_timeout=0;
}
```

### Schritt 3: Konfiguration aktivieren

```bash
# Symlink erstellen
sudo ln -s /etc/nginx/sites-available/chrani-bot-tng /etc/nginx/sites-enabled/

# Standard-Site deaktivieren (optional)
sudo rm /etc/nginx/sites-enabled/default

# Konfiguration testen
sudo nginx -t

# Bei erfolgreicher Prüfung:
sudo systemctl reload nginx
```

### Schritt 4: Firewall konfigurieren

```bash
# ufw (Ubuntu/Debian)
sudo ufw allow 'Nginx Full'
sudo ufw enable

# firewalld (CentOS/RHEL/Fedora)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Schritt 5: SSL-Zertifikat mit Let's Encrypt (optional)

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
# sudo yum install certbot python3-certbot-nginx  # CentOS

# Zertifikat erstellen (interaktiv)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Automatische Erneuerung testen
sudo certbot renew --dry-run
```

### Schritt 6: Zugriff testen

```bash
# HTTP (sollte zu HTTPS umleiten)
curl -I http://your-domain.com

# HTTPS
curl -I https://your-domain.com
```

Im Browser: `https://your-domain.com`

---

## Systemd-Service einrichten

Mit systemd läuft chrani-bot-tng als System-Service, startet automatisch beim Booten und wird bei Fehlern neu gestartet.

### Schritt 1: Service-Datei anpassen

```bash
# Service-Datei bearbeiten
nano chrani-bot-tng.service
```

**Wichtige Anpassungen**:

```ini
# Benutzer und Gruppe ändern
User=your-username
Group=your-username

# Pfade anpassen
WorkingDirectory=/home/your-username/chrani-bot-tng
Environment="PATH=/home/your-username/chrani-bot-tng/venv/bin"
ExecStart=/home/your-username/chrani-bot-tng/venv/bin/gunicorn -c gunicorn.conf.py wsgi:application
```

### Schritt 2: Service installieren

```bash
# Service-Datei nach systemd kopieren
sudo cp chrani-bot-tng.service /etc/systemd/system/

# systemd neu laden
sudo systemctl daemon-reload

# Service aktivieren (Autostart beim Booten)
sudo systemctl enable chrani-bot-tng

# Service starten
sudo systemctl start chrani-bot-tng
```

### Schritt 3: Service-Status prüfen

```bash
# Status anzeigen
sudo systemctl status chrani-bot-tng

# Logs anzeigen
sudo journalctl -u chrani-bot-tng -f

# Logs der letzten Stunde
sudo journalctl -u chrani-bot-tng --since "1 hour ago"
```

### Schritt 4: Service-Befehle

```bash
# Service stoppen
sudo systemctl stop chrani-bot-tng

# Service neu starten
sudo systemctl restart chrani-bot-tng

# Service neu laden (bei Konfigurationsänderungen)
sudo systemctl reload chrani-bot-tng

# Autostart deaktivieren
sudo systemctl disable chrani-bot-tng
```

---

## Fehlerbehebung

### Problem: "Module not found" Fehler

**Symptom**: ImportError beim Starten

**Lösung**:
```bash
# Virtual Environment aktiviert?
source venv/bin/activate

# Dependencies neu installieren
pip install -r requirements.txt

# Python-Version prüfen (mindestens 3.8)
python3 --version
```

### Problem: Port bereits in Benutzung

**Symptom**: "Address already in use"

**Lösung**:
```bash
# Prozess auf Port 5000 finden
sudo lsof -i :5000

# Oder mit netstat
sudo netstat -tulpn | grep :5000

# Prozess beenden
sudo kill -9 <PID>

# Oder anderen Port in gunicorn.conf.py verwenden
```

### Problem: WebSocket-Verbindung schlägt fehl

**Symptom**: "WebSocket connection failed" im Browser

**Lösung**:
1. Prüfen Sie, dass nur 1 Worker in `gunicorn.conf.py` konfiguriert ist:
   ```python
   workers = 1
   worker_class = "gevent"
   ```

2. nginx-Konfiguration prüfen (WebSocket-Headers):
   ```nginx
   location /socket.io/ {
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

### Problem: 502 Bad Gateway (nginx)

**Symptom**: nginx zeigt "502 Bad Gateway"

**Lösung**:
```bash
# Ist gunicorn gestartet?
sudo systemctl status chrani-bot-tng

# Logs prüfen
sudo journalctl -u chrani-bot-tng -n 50

# nginx-Fehlerlog prüfen
sudo tail -f /var/log/nginx/chrani-bot-tng-error.log

# Upstream in nginx.conf prüfen
# Stimmt IP und Port mit gunicorn überein?
```

### Problem: Hohe CPU-Last

**Symptom**: Server reagiert langsam, CPU bei 100%

**Lösung**:
```bash
# Prozesse prüfen
top -u your-username

# gunicorn-Worker-Anzahl anpassen (aber max. 1 für WebSocket!)
# Timeout erhöhen in gunicorn.conf.py
timeout = 300

# Logs auf Endlosschleifen prüfen
sudo journalctl -u chrani-bot-tng -f
```

### Problem: Telnet-Verbindung zum Gameserver schlägt fehl

**Symptom**: Bot kann sich nicht mit dem 7 Days to Die Server verbinden

**Lösung**:
1. Telnet-Einstellungen prüfen:
   ```bash
   nano bot/options/module_telnet.json
   ```

2. Verbindung manuell testen:
   ```bash
   telnet <gameserver-ip> <telnet-port>
   # Passwort eingeben
   ```

3. Firewall-Regeln prüfen
4. Gameserver-Konfiguration prüfen (telnet aktiviert?)

---

## Wartung und Updates

### Code-Updates einspielen

```bash
# Zum Projektverzeichnis
cd ~/chrani-bot-tng

# Änderungen abrufen
git fetch origin

# Aktuellen Branch prüfen
git branch

# Updates herunterladen und anwenden
git pull origin main  # oder Ihr Branch-Name

# Dependencies aktualisieren
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Service neu starten
sudo systemctl restart chrani-bot-tng
```

### Backup erstellen

```bash
# Gesamtes Projektverzeichnis sichern
tar -czf chrani-bot-tng-backup-$(date +%Y%m%d).tar.gz ~/chrani-bot-tng

# Nur Konfiguration sichern
tar -czf chrani-bot-config-backup-$(date +%Y%m%d).tar.gz ~/chrani-bot-tng/bot/options

# Backup an sicheren Ort verschieben
mv chrani-bot-*.tar.gz /path/to/backup/location/
```

### Logs rotieren

nginx rotiert Logs automatisch. Für gunicorn/systemd:

```bash
# Log-Größe prüfen
sudo journalctl --disk-usage

# Alte Logs löschen (älter als 7 Tage)
sudo journalctl --vacuum-time=7d

# Oder nach Größe (maximal 500 MB behalten)
sudo journalctl --vacuum-size=500M
```

### Performance-Monitoring

```bash
# Systemressourcen überwachen
htop

# Nur chrani-bot-tng Prozesse
htop -u your-username

# Netzwerk-Verbindungen prüfen
sudo netstat -tulpn | grep gunicorn

# Echtzeit-Logs
sudo journalctl -u chrani-bot-tng -f
```

---

## Zusammenfassung der Befehle

### Lokaler Test (Schnellstart)

```bash
# Setup
git clone <repository-url>
cd chrani-bot-tng
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Starten
gunicorn -c gunicorn.conf.py wsgi:application

# Stoppen: STRG+C
```

### Produktions-Deployment

```bash
# Einmalige Einrichtung
sudo cp chrani-bot-tng.service /etc/systemd/system/
sudo cp nginx.conf.example /etc/nginx/sites-available/chrani-bot-tng
sudo ln -s /etc/nginx/sites-available/chrani-bot-tng /etc/nginx/sites-enabled/
sudo systemctl daemon-reload
sudo systemctl enable chrani-bot-tng
sudo systemctl enable nginx

# Starten
sudo systemctl start chrani-bot-tng
sudo systemctl start nginx

# Status
sudo systemctl status chrani-bot-tng
sudo journalctl -u chrani-bot-tng -f
```

---

## Weitere Ressourcen

- **Gunicorn Dokumentation**: https://docs.gunicorn.org/
- **nginx Dokumentation**: https://nginx.org/en/docs/
- **Flask-SocketIO Dokumentation**: https://flask-socketio.readthedocs.io/
- **systemd Dokumentation**: https://www.freedesktop.org/software/systemd/man/

---

## Support

Bei Problemen:

1. Prüfen Sie die Logs: `sudo journalctl -u chrani-bot-tng -n 100`
2. Suchen Sie in den GitHub Issues
3. Erstellen Sie ein neues Issue mit:
   - Fehlermeldung
   - Logs
   - Systeminfo (OS, Python-Version, etc.)

---

**Viel Erfolg mit chrani-bot-tng!** 🚀
