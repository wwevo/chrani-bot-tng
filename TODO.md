# TODO Liste - chrani_bot_tng
**Roadmap zu 1.0 Alpha**

Diese Liste ist nach Priorität sortiert. Kritische und hochpriorisierte Bugs sollten vor dem Alpha-Release behoben sein.

---

## ✅ KÜRZLICH BEHOBEN

### Teleport-System komplett überarbeitet (Event-based)
- **Problem**: Blocking Teleports mit Sleep → Timeouts, Race-Conditions
- **Lösung**: Event-based Teleport mit pending_teleports Registry
- **Betroffene Dateien**:
  - `bot/modules/players/__init__.py` - pending_teleports Registry + Timeout-Watcher
  - `bot/modules/players/actions/teleport_player.py` - Non-blocking Implementierung
  - `bot/modules/players/triggers/playerspawn.py` - Event-Handler für Teleport-Completion
- **Status**: ✅ Gelöst - Teleports sind instant (~140ms), keine Blocking mehr

### Regex-Bug in playerspawn.py behoben
- **Problem**: PlayerName-Regex zu gierig → Bot sagt "ECV', ClientNumber='19'"
- **Lösung**: `(?P<player_name>.*)` → `(?P<player_name>[^']+)` (2 Stellen)
- **Status**: ✅ Gelöst - Zeile 150 + 162

### Logger-Formatierung verbessert
- **Problem**: `reason=list[1]`, `target_pos=dict[3]` → unleserlich bei Fehlern
- **Lösung**: Kleine Collections (≤3 Elemente) werden ausgeschrieben, große kompakt als type[length]
- **Betroffene Datei**: `bot/logger.py` (Zeile 185-197)
- **Status**: ✅ Gelöst

### Diagnostic-Logging-System implementiert
- **Features**:
  - File-based Logging (all.log, errors.log, telnet_raw.log, actions.log)
  - Raw Telnet Data Logging für Server/Bot-Datenabgleich
  - Debug-Level Logging (opt-in)
  - Graceful Shutdown mit Signal-Handlers
- **Neue Dateien**:
  - `start_with_diagnostics.py` - Startup-Script mit Diagnostics
  - `.run/app-diagnostics.run.xml` - IntelliJ Run-Konfiguration
  - `DIAGNOSTICS.md` - Ausführliche Dokumentation
- **Status**: ✅ Implementiert

---

## 🔴 KRITISCH - Muss vor 1.0 Alpha behoben werden

### Race-Conditions bei Player-Disconnect (teilweise behoben)

#### 1. FELLTHROUGHWORLD-Teleport-Loop (teilweise behoben)
- **Problem**: Bot teleportiert mit Y=0 → Spieler fällt durch Welt
- **Status**: Teleport-System ist jetzt event-based (✅), aber Y-Koordinaten-Validierung fehlt noch
- **Betroffene Dateien**:
  - `bot/modules/players/actions/teleport_player.py` (Zeile 58-59) - verwendet bereits Y=-1 Fallback
  - Templates bereits gefixt: Y=-1 als Default
- **Noch zu tun**: Y-Validierung beim Speichern von Locations (UI-seitig)

#### 2. Race-Conditions bei Player-Disconnect
- **Problem**: Trigger feuern auf bereits disconnected Players → timeout/fail
- **Impact**: Error-Spam in Logs, schlechte Performance
- **Root Cause**: Telnet-Events kommen NACH Socket-Disconnect, Trigger haben keinen Online-Check
- **Verstärkung durch FELLTHROUGHWORLD**: Mehr Position-Updates = mehr Race-Conditions
- **Betroffene Dateien**:
  - `bot/modules/permissions/triggers/player_moved.py` (Zeile 8-51)
  - `bot/modules/permissions/triggers/player_authentication_change.py` (Zeile 8-32)
  - `bot/modules/players/actions/teleport_player.py`
  - `bot/modules/players/actions/say_to_player.py`
  - `bot/modules/players/actions/toggle_player_mute.py`
  - `bot/modules/players/actions/toggle_player_authentication.py`
- **Lösung (Umfassend)**: Telnet-Buffer mit Timestamps + Event-Verwerfung

#### 3. Player-Actions: Online-Status nicht validiert (teilweise behoben)
- **Problem**: Actions prüfen nur `player_entity_id`, nicht `is_online`
- **Impact**: Actions failen auf Player im Login-Prozess
- **Status**: teleport_player.py hat bereits Online-Check (✅)
- **Noch betroffene Actions**:
  - `say_to_player.py` (Zeile 27-31)
  - `kick_player.py` (Zeile 35-37)
  - `toggle_player_mute.py` (Zeile 27-29)
- **Lösung**: `is_online` Flag vor entity_id-Check prüfen + `fail_reason` setzen

### UI/UX Critical Issues

#### 4. Sporadisches Silent-Fail bei Widget-Button-Klicks
- **Problem**: Admin klickt Button, nichts passiert, kein Log
- **Impact**: User weiß nicht, dass Browser-Reload nötig ist → für ihn ist alles "kaputt"
- **Betroffene Datei**: `bot/modules/webserver/__init__.py` (Zeile 582)
- **Analyse**: Race-Condition bei Multi-Socket-Sessions?

---

## 🟠 HOCH - Sollte vor 1.0 Alpha behoben werden

### Logging-System verbessern (zusammenhängend)

Diese Probleme machen Debugging schwierig und produzieren unklare Error-Logs.

#### 5. System-Actions im Error-Log unklar gekennzeichnet
- **Problem**: `user=null` statt `user=system` → unklar ob automatisch oder User-Action
- **Betroffene Datei**: `bot/module.py` (Zeile 95-103)
- **Lösung**: In Zeile 101 `user=null` → `user=system`

#### 6. fail_reason als Liste wird falsch geloggt (teilweise behoben)
- **Problem**: `reason=list[1]` statt tatsächlicher Fehler im Log
- **Status**: Logger zeigt jetzt kleine Listen (≤3 Elemente) aus (✅)
- **Noch zu tun**: Actions sollten `fail_reason` als String statt Liste setzen
- **Betroffene Actions**: `update_player_permission_level.py` (Zeile 14, 40-42)
- **Lösung**: In Actions direkt String verwenden statt Liste

#### 7. Race-Condition beim Systemstart
- **Problem**: Actions failen beim Start weil Dependencies nicht geladen (getadmins → admins_updated → update_player_permission_level failt)
- **Impact**: Unnötige Error-Logs beim Start
- **Betroffene Module**: `players/__init__.py`, `game_environment/__init__.py`
- **Lösung 1**: Error-Logs nur wenn Gameserver "ready"
- **Lösung 2**: Dependency-Chain für Actions
- **Lösung 3**: Trigger prüft ob `active_dataset` existiert

#### 8. Doppelte active_dataset_set Log-Meldungen
- **Problem**: `getgameprefs` wird zweimal ausgeführt bevor `disable_after_success` greift
- **Betroffene Datei**: `game_environment/__init__.py` (Zeile 82-84)
- **Lösung**: Action-Status vor Aufruf prüfen oder Flag im DOM setzen

### Permission-System halbfertig

#### 9. Permission-Error-Handling-System überarbeiten
- **Problem**: Actions werden IMMER ausgeführt, auch bei `permission_denied`
- **Impact**: ERROR-Logs mit `reason=unknown` statt `reason=permission`
- **Betroffene Datei**: `bot/modules/permissions/__init__.py` (Zeile 189)
- **Lösung**: Entweder zentral in Permissions abbrechen ODER alle Actions müssen `has_permission` prüfen

### Telnet-Modul

#### 10. Telnet-Line-Validation: WRN/ERR nicht akzeptiert
- **Problem**: `telnet_invalid_line_start` Warnings für valide WRN/ERR Lines
- **Betroffene Datei**: `bot/modules/telnet/__init__.py` (Zeile 41)
- **Lösung**: Pattern erweitern: `r"...\s(?P<log_level>INF|WRN|ERR) .*"`

---

## 🟡 MITTEL - Nice to have für 1.0 Alpha

### UI/UX Verbesserungen

#### 11. SteamID und Name neben Log-Out-Button anzeigen
- **Betroffenes Modul**: Webserver

#### 12. SteamID beim Hover des Log-In-Buttons entfernen
- **Betroffenes Modul**: Webserver

#### 13. "You are here x y z"-Tafel entfernen
- **Betroffene Datei**: `bot/modules/locations/templates/manage_locations_widget/control_player_location.html`

---

## 🟢 NIEDRIG - Nach 1.0 Alpha

### Code-Qualität und Refactoring

#### 14. Delete-Modal-System vereinheitlichen
- **Problem 1**: Platzhalter "Element 1-40" statt echte Element-Liste
- **Problem 2**: Code-Duplikation in 4 Widgets
- **Betroffene Datei**: `bot/modules/dom_management/templates/modal_confirm_delete.html`
- **Lösung**: Zwei neue Methoden in `bot/mixins/widget.py`:
  - `count_selected_elements(dispatchers_steamid)`
  - `get_delete_button_and_modal(dispatchers_steamid, dom_element_id_prefix)`
- **Vorteil**: ~100+ Zeilen Code eliminiert, konsistente Funktionalität

#### 15. Template-Dateien mit Jinja2-Blocks konsolidieren
- **Problem**: 93 HTML-Dateien, viele zusammengehörige Templates
- **Betroffene Module**: locations (24), telnet (12), players (12), game_environment (7), webserver (6), example_checkboxes (6)
- **Lösung**: Jinja2 Named Blocks - mehrere Templates in einer Datei
- **Vorteil**: Bessere Lesbarkeit, trotzdem granulare Updates

#### 16. Code-Kommentare auf Nützlichkeit prüfen
- **Problem**: Sinnlose Kommentare wie "sets variable" oder "start loop"
- **Lösung**: Alle Kommentare durchgehen, triviale entfernen

---

## 📋 Ablaufplan für 1.0 Alpha

**Phase 1: Kritische Bugs**
1. FELLTHROUGHWORLD Quick Fix
2. Online-Check in player_moved.py + player_authentication_change.py
3. Online-Status-Validierung in 4 Player-Actions
4. Silent-Fail bei Widget-Button-Klicks beheben
5. Tests: Teleport + Disconnect-Szenarien

**Phase 2: Logging-Verbesserungen**
5. System-Actions kennzeichnen
6. fail_reason Listen-Handling
7. Race-Condition beim Start beheben
8. Doppelte Logs beheben

**Phase 3: Permission + Telnet**
9. Permission-System überarbeiten
10. Telnet WRN/ERR Pattern

**Phase 4: UI/UX (optional)**
11-13. Webserver UI-Verbesserungen

Nach 1.0 Alpha können die Code-Qualität-TODOs (14-16) angegangen werden.
