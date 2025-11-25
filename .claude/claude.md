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

**Wichtig: Die Hauptliste und ihre Steuerung muss ins Modul!**
- Widget = dünner Wrapper für Template-Rendering
- `<modul>/__init__.py` = dicke Logik für Listen-Management
- Widget ruft Modul-Funktionen auf, implementiert sie nicht selbst

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

---

## Implementierungs-Patterns

### Widget Update-Funktionen

**Pattern:** Widget-Funktion ruft Modul-Funktion auf (wie `update_delete_button_status`)

```python
# ✓ RICHTIG: Widget (dünner Wrapper)
def update_xyz_status(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    sanitized_dataset = module.<base_module>.sanitize_for_html_id(updated_values_dict["dataset"])

    module.<base_module>.update_xyz_status(
        *args, **kwargs,
        target_module=module,
        dom_element_id={
            "id": "element_{}_xyz".format(sanitized_dataset)
        }
    )

# ✗ FALSCH: Gesamte Logik im Widget
def update_xyz_status(*args, **kwargs):
    # 40+ Zeilen Business-Logik hier...
    # Listen durchlaufen, Status berechnen, etc.
```

**Regel:** Mehr als 10 Zeilen Logik? → Gehört ins Modul!

---

### Parameter-Naming-Konventionen

**Projekt-Konventionen einhalten, KEINE custom names!**

```python
# ✓ RICHTIG
dom_element_entry_selected=all_elements_selected
dom_element_select_root=["selected_by"]
dom_element_id={"id": "..."}
dom_element_root=module.dom_element_root

# ✗ FALSCH
all_elements_selected=all_elements_selected  # custom name!
select_root=["selected_by"]  # zu kurz!
element_id="..."  # falsche Struktur!
```

**Wichtig:** Immer bestehende Funktionen als Vorbild nehmen (`update_delete_button_status`, `get_selection_dom_element`)

---

### ID-Konventionen

**IDs müssen dataset-spezifisch sein bei Multi-Dataset-Modulen!**

```python
# ✓ RICHTIG
id="element_table_{sanitized_dataset}_control"

# ✗ FALSCH
id="element_table_control"  # global, nicht dataset-spezifisch!
```

**Format:** `{prefix}_{sanitized_dataset}_{suffix}`

---

### Socket send_data_to_client_hook Parameter

**Standard-Parameter für Element-Updates:**

```python
# ✓ RICHTIG
module.webserver.send_data_to_client_hook(
    module,
    payload=element_content,
    data_type="element_content",
    clients=[dispatchers_steamid],
    method="replace",
    target_element=dom_element_id  # dict mit {"id": "..."}
)

# ✗ FALSCH
module.webserver.send_data_to_client_hook(
    module,
    payload=element_content,
    data_type="dom_element_update",  # falscher type!
    clients=[clientid],
    target_element={
        "id": "...",
        "type": "span",  # unnötig!
        "selector": "..."  # unnötig!
    }
)
```

**Regel:** `target_element` ist ein dict mit nur `{"id": "..."}`, keine zusätzlichen keys!

---

### Callback-Handler

**KEIN Multi-Client Loop in Callback-Funktionen!**

```python
# ✓ RICHTIG: Nur dispatchers_steamid
def update_xyz_status(*args, **kwargs):
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
    # Funktion wird pro Client aufgerufen!

# ✗ FALSCH: Loop über alle Clients
def update_xyz_status(*args, **kwargs):
    for clientid in module.webserver.connected_clients.keys():
        # Callback wird bereits für jeden Client aufgerufen!
```

**Regel:** Die Callback-Funktion wird bereits pro betroffenem Client aufgerufen. Kein eigener Loop nötig!

---

### Modul-Funktionen implementieren

**Logik-schwere Funktionen gehören in `<modul>/__init__.py`**

**Struktur:**
```python
def update_xyz_status(self, *args, **kwargs):
    module = args[0]
    dom_element_id = kwargs.get("dom_element_id", None)
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    # 1. Daten aus module.dom.data holen
    # 2. Status berechnen (Listen durchlaufen, zählen, etc.)
    # 3. Element neu rendern (get_xyz_dom_element)
    # 4. Via Socket senden (send_data_to_client_hook)
```

**Vorbild:** `update_delete_button_status` in Base-Modul

---

### Single Responsibility Principle

**Klare Trennung:**

| Schicht | Verantwortung | Beispiel |
|---------|---------------|----------|
| **Widget** | Template-Orchestrierung | Welches Template? Welche Variablen? |
| **Modul** | CORE-Business-Logik | Listen durchlaufen, Status berechnen |
| **Template** | Darstellung | HTML-Struktur, Makro-Aufrufe |
| **Action** | Datenbank-Manipulation | Upsert, Validierung |

**Merksatz:** Widget = Wrapper, Modul = Logik, Template = View, Action = Model
