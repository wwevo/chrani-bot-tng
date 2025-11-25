# Projektrichtlinien - Chrani-Bot-TNG

## Hauptziel
**Core-Funktionen der Module fertigstellen für homogenes Management vom CRUD Workflow**

Konkret: Select- und Delete-Funktionen auf Low-Level-Ebene ausbauen, sodass alle Änderungen automatisch für alle Module gelten.

## Architektur-Prinzipien

### 1. **Base-Klassen-Fokus**
- Alle Lösungen konzentrieren sich auf die Base-Klassen
- Änderungen auf Low-Level-Ebene → automatische Vererbung für alle Module
- DRY: Keine Duplizierung in einzelnen Modulen

### 2. **Widget-Verantwortlichkeiten**
- In Widgets: **Widget-Business-Logik** (spezifisch für dieses Widget) + Template-Steuerung
- **KEINE CORE-Business-Logik** in Widgets
- **Beispiel:** Players Widget hat Code für Players (Widget-spezifisch)
  - ✓ Widget-Business-Logik: Player-spezifische Funktionen
  - ✗ CORE-Logik: Listenlogik für ALLE Modul-Listen gehört in Base-Klassen
- Widgets orchestrieren nicht nur, sie haben durchaus eigene Logik
- Sie kümmern sich aber **nicht um übergreifende Funktionen**

### 3. **Event-System (Socket.IO)**
- Alle Aktionen (Schaltflächen, Links, Buttons) laufen über das Event-System
- Socket.IO als zentraler Kommunikationskanal
- Reaktives System: alles funktioniert nach dem selben Schema

### 4. **Template-System**
- Mehrere Templates erforderlich
- Alle Links werden über entsprechende **Template-Makros** erstellt
- Keine hartcodierten URLs/Links

### 5. **Kommunikationswege** ⭐ **KERNSTÜCK**

#### **Browser ↔ Socket Cycle (Reaktive Wechselkommunikation):**

```
1. Browser redet mit Socket
2. Socket schickt an Browser
3. Browser präsentiert UI
4. Nutzer wählt Aktion
5. Aktion geht per Socket an Widget
   ↓
   ┌─────────────────────────────────────────────┐
   │ PATH A: Datenbank-gesteuert (mit Callbacks) │
   └─────────────────────────────────────────────┘
   6a. Widget arbeitet → schreibt in Datenbank
   7a. Datenbank ruft mittels Callback alle beteiligten Module auf
   8a. Modul schickt mittels Socket an Browser

   ┌─────────────────────────────┐
   │ PATH B: Direkte Aktion      │
   └─────────────────────────────┘
   6b. Widget arbeitet → führt direkt Aktion aus
   7b. Modul schickt mittels Socket an Browser

→ Cycle complete: zurück zu Schritt 2
```

#### **Server-interne Kommunikation:**
- Commands, Triggers und Actions vom Server kommunizieren **lokal**
- Und senden dann an den Browser

## Referenz-Implementierung
**manage_entities_widget im game_environment Modul** dient als kompaktes Beispiel

---

## Projektvorgehen
**Langfristig:** Viel Modularität + weniger Boilerplate

**Aber zuerst (aktuelle Phase):**
1. ✓ Alle Funktionen müssen erstmal da sein
2. → Dann testen
3. → Dann optimieren

---

## Entwicklungsrichtlinien

### Code-Organisation
- Widget-spezifische Logik bleibt in Widgets
- Übergreifende Funktionalität gehört in Base-Klassen
- Keine Code-Duplizierung zwischen Modulen

### Template-Konventionen
- Alle interaktiven Elemente (Links, Buttons) über Template-Makros
- Konsistente Verwendung des Event-Systems
- Reaktive Updates über Socket.IO

### Testing-Strategie
1. Funktionalität komplett implementieren
2. Gründlich testen
3. Dann optimieren und refactoren
