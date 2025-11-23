# Command Tracking System - Implementation Plan

**Branch:** `claude/20251123-better-logging`

**Ziel:** End-to-end tracking von Commands (initial: `lp`) um Delays zu identifizieren (3-5s Teleport, 10-12s Webmap).

**Aktivierung:** Nur wenn `PROFILING_ENABLED=True` + `debug_id` in action_meta gesetzt.

---

## Output Format

**Datei:** `bot/diagnostic_logs/command_tracking_{debug_id}_{timestamp}.json`

```json
{
  "command": "lp",
  "test_duration": 32.5,
  "commands_queued": 10,
  "commands_sent": 10,
  "command_results_matched": 10,
  "timeline": [
    {"ts": "2025-11-23T08:33:21.123456", "event": "QUEUED", "id": "A4B2C1D3", "q_high": 0, "q_normal": 1, "q_low": 0},
    {"ts": "2025-11-23T08:33:21.148", "event": "SENT_TO_SERVER", "id": "A4B2C1D3"},
    {"ts": "2025-11-23T08:33:21.979", "event": "RESPONSE_RECEIVED", "id": "A4B2C1D3", "player_count": 1},
    {"ts": "2025-11-23T08:33:21.980", "event": "CALLBACK_SUCCESS", "id": "A4B2C1D3", "action": "getplayers"},
    {"ts": "2025-11-23T08:33:21.983", "event": "WEBSOCKET_SEND", "id": "A4B2C1D3", "steamid": "76561...", "clients": 1},
    {"ts": "2025-11-23T08:33:22.018", "event": "BROWSER_RECEIVED", "steamid": "76561..."},
    {"ts": "2025-11-23T08:33:22.020", "event": "MARKER_UPDATED", "steamid": "76561..."}
  ]
}
```

**Was auswerten:**
- `QUEUED` → `SENT_TO_SERVER` = Queue-Delay
- `SENT_TO_SERVER` → `RESPONSE_RECEIVED` = Telnet-Server Antwortzeit
- `RESPONSE_RECEIVED` → `CALLBACK_SUCCESS` = Callback-Verarbeitung
- `CALLBACK_SUCCESS` → `WEBSOCKET_SEND` = DOM-Update
- `WEBSOCKET_SEND` → `BROWSER_RECEIVED` = Network/WebSocket Latenz
- `BROWSER_RECEIVED` → `MARKER_UPDATED` = Browser Rendering

---

## Dateien die geändert werden

### 1. bot/tracking.py (neu)

**Zweck:** Zentrales Tracking-System

```python
import os
import json
from datetime import datetime
from collections import defaultdict

class CommandTracker:
    def __init__(self):
        self._enabled = os.getenv('PROFILING_ENABLED', '').lower() == 'true'
        self._command_to_id = {}  # {"lp": "A4B2C1D3"}
        self._tracking_commands = {}  # {"lp": True}
        self._events = []
        self._stats = defaultdict(int)
        self._test_start = None
        self._log_file = None
        self._debug_id = None

    def should_track(self, debug_id):
        return self._enabled and debug_id in self._tracking_commands

    def start_tracking(self, debug_id):
        """Called when first command with debug_id is queued."""
        if not self._enabled:
            return

        self._debug_id = debug_id
        self._tracking_commands[debug_id] = True
        self._test_start = datetime.now()

        timestamp = self._test_start.strftime('%Y%m%d_%H%M%S')
        log_dir = os.path.join(os.path.dirname(__file__), 'diagnostic_logs')
        os.makedirs(log_dir, exist_ok=True)
        self._log_file = os.path.join(log_dir, f'command_tracking_{debug_id}_{timestamp}.json')

    def register_command(self, command, tracking_id):
        """Store tracking_id for command string."""
        self._command_to_id[command] = tracking_id

    def get_tracking_id(self, command):
        """Get tracking_id for command string."""
        return self._command_to_id.get(command)

    def log_event(self, event_type, tracking_id=None, **kwargs):
        if not self._enabled:
            return

        self._events.append({
            "ts": datetime.now().isoformat(),
            "event": event_type,
            "id": tracking_id,
            **kwargs
        })

    def increment_stat(self, stat_name):
        if self._enabled:
            self._stats[stat_name] += 1

    def write_results(self):
        """Write final results. Call after test completes."""
        if not self._enabled or not self._log_file:
            return

        test_duration = (datetime.now() - self._test_start).total_seconds()

        output = {
            "command": self._debug_id,
            "test_duration": test_duration,
            "commands_queued": self._stats['queued'],
            "commands_sent": self._stats['sent'],
            "command_results_matched": self._stats['matched'],
            "timeline": self._events
        }

        with open(self._log_file, 'w') as f:
            json.dump(output, f, indent=2)

tracker = CommandTracker()
```

### 2. bot/mixins/action.py

**Änderung:** tracking_id generieren wenn `debug_id` in action_meta

```python
# In trigger_action(), nach uuid4 generation:
if action_is_enabled:
    event_data[1]["module"] = target_module.getName()
    event_data[1]["uuid4"] = target_module.id_generator(22)

    # Add tracking_id if debug_id is set
    debug_id = active_action.get("debug_id")
    if debug_id:
        event_data[1]["tracking_id"] = target_module.id_generator(8)
        event_data[1]["debug_id"] = debug_id

    # ... rest of code
```

### 3. bot/modules/telnet/__init__.py

**Änderung 1:** In `add_telnet_command_to_queue()` - tracking loggen + ID registrieren

```python
def add_telnet_command_to_queue(self, command, action_meta=None, priority='normal'):
    from bot.tracking import tracker

    # Extract priority
    if action_meta and 'command_priority' in action_meta:
        priority = action_meta['command_priority']

    # Get tracking info from action_meta (passed through from trigger_action via event_data)
    tracking_id = action_meta.get('tracking_id') if action_meta else None
    debug_id = action_meta.get('debug_id') if action_meta else None

    added = self.telnet_command_queue.add_command(command, priority)

    # Track if enabled
    if added and tracker.should_track(debug_id):
        # First command? Start tracking
        if tracker._test_start is None:
            tracker.start_tracking(debug_id)

        # Register command → tracking_id mapping
        tracker.register_command(command, tracking_id)

        # Log event
        tracker.log_event("QUEUED", tracking_id,
            q_high=len(self.telnet_command_queue.queues['high']),
            q_normal=len(self.telnet_command_queue.queues['normal']),
            q_low=len(self.telnet_command_queue.queues['low'])
        )
        tracker.increment_stat('queued')

    # ... rest of existing code (high priority execution)
    if added and priority == 'high':
        self._execute_high_priority_batch()

    return added
```

**Änderung 2:** In `execute_telnet_command_queue()` - tracking_id lookup + loggen

```python
def execute_telnet_command_queue(self, this_many_lines):
    from bot.profiler import profiler
    from bot.tracking import tracker

    with profiler.measure("telnet_execute_queue"):
        batch = self.telnet_command_queue.get_next_batch(max_total=this_many_lines)

        for telnet_command, priority in batch:
            command = f"{telnet_command}\r\n"

            try:
                self.tn.write(command.encode('ascii'))

                # Track if this command is being tracked
                tracking_id = tracker.get_tracking_id(telnet_command)
                if tracking_id:
                    tracker.log_event("SENT_TO_SERVER", tracking_id)
                    tracker.increment_stat('sent')

            except Exception as error:
                # ... existing error handling
```

**WICHTIG:** `action_meta` muss von `getplayers.py` an `add_telnet_command_to_queue()` durchgereicht werden!

### 4. bot/modules/players/actions/getplayers.py

**Änderung 1:** In `main_function()` - action_meta an queue übergeben

```python
def main_function(module, event_data, dispatchers_steamid=None):
    timeout = TELNET_TIMEOUT_SHORT
    timeout_start = time()
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    # Get action_meta to pass tracking info
    action_meta_dict = action_meta.copy()
    action_meta_dict['tracking_id'] = event_data[1].get('tracking_id')
    action_meta_dict['debug_id'] = event_data[1].get('debug_id')

    if module.telnet.add_telnet_command_to_queue("lp", action_meta=action_meta_dict):
        poll_is_finished = False
        # ... existing regex code
```

**Änderung 2:** Nach regex match - response loggen

```python
if match:
    from bot.tracking import tracker

    tracking_id = event_data[1].get("tracking_id")
    debug_id = event_data[1].get("debug_id")

    if tracker.should_track(debug_id):
        tracker.log_event("RESPONSE_RECEIVED", tracking_id,
            player_count=int(match.group("player_count"))
        )
        tracker.increment_stat('matched')

    module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
    return
```

**Änderung 3:** action_meta - `debug_id` hinzufügen

```python
action_meta = {
    "description": "gets a list of all currently logged in players and sets status-flags",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "skip_it": skip_it,
    "requires_telnet_connection": True,
    "enabled": True,
    "debug_id": "lp"  # <-- Enable tracking
}
```

### 5. bot/module.py

**Änderung 1:** In `callback_success()` - Tracking loggen

```python
@staticmethod
def callback_success(callback, module, event_data, dispatchers_steamid, match=None):
    from bot.tracking import tracker

    event_data[1]["status"] = "success"

    tracking_id = event_data[1].get("tracking_id")
    debug_id = event_data[1].get("debug_id")

    if tracker.should_track(debug_id):
        tracker.log_event("CALLBACK_SUCCESS", tracking_id,
            action=event_data[1].get("action_identifier")
        )

    # ... rest of existing code
    action_identifier = event_data[1]["action_identifier"]
    if event_data[1].get("disable_after_success"):
        module.disable_action(action_identifier)

    module.emit_event_status(module, event_data, dispatchers_steamid, event_data[1])
    callback(module, event_data, dispatchers_steamid, match)
```

**Änderung 2:** In `callback_fail()` - Tracking loggen

```python
@staticmethod
def callback_fail(callback, module, event_data, dispatchers_steamid):
    from bot.tracking import tracker

    event_data[1]["status"] = "fail"

    tracking_id = event_data[1].get("tracking_id")
    debug_id = event_data[1].get("debug_id")

    if tracker.should_track(debug_id):
        tracker.log_event("CALLBACK_FAIL", tracking_id,
            reason=event_data[1].get("fail_reason")
        )

    # ... rest of existing code
    logger.error("action_failed",
                module=module.name,
                action=event_data[0],
                reason=event_data[1].get("fail_reason", "unknown"),
                uuid4=event_data[1].get("uuid4"))

    module.emit_event_status(module, event_data, dispatchers_steamid, event_data[1])
    callback(module, event_data, dispatchers_steamid)
```

### 6. bot/modules/players/triggers/player_update_on_map.py

**Änderung:** Nach WebSocket send - tracking loggen

```python
module.webserver.send_data_to_client_hook(
    module,
    payload=player_update_data,
    data_type="player_position_update",
    clients=[clientid]
)

# Track websocket sends
from bot.tracking import tracker
if tracker.should_track("lp"):  # Hardcoded for now - could be improved
    tracker.log_event("WEBSOCKET_SEND", None,  # No tracking_id at this point
        steamid=steamid,
        clients=len(module.webserver.connected_clients)
    )
```

### 7. bot/modules/webserver/__init__.py

**Änderung 1:** Profiling status endpoint

```python
@socketio.on('get_profiling_status')
def handle_profiling_status():
    import os
    emit('profiling_status', {
        'enabled': os.getenv('PROFILING_ENABLED', '').lower() == 'true'
    })
```

**Änderung 2:** Browser tracking results endpoint

```python
@socketio.on('tracking_results')
def handle_tracking_results(data):
    from bot.tracking import tracker

    if not tracker._enabled:
        return

    # Append browser events to timeline
    for event in data.get('events', []):
        tracker._events.append(event)

    # Write final results
    tracker.write_results()
```

### 8. bot/modules/webserver/static/system.js

**Änderung 1:** Bei connect - profiling status abfragen

```javascript
// Connection established
window.socket.on('connect', function() {
    console.log('[SOCKET] Connected, SID:', socket.id);
    // ... existing code ...

    // Check if profiling enabled
    window.socket.emit('get_profiling_status');
});

// Profiling status response
window.socket.on('profiling_status', function(data) {
    window.PROFILING_ENABLED = data.enabled;
    if (window.PROFILING_ENABLED) {
        window.trackingEvents = [];
        console.log('[TRACKING] Profiling enabled');
    }
});
```

**Änderung 2:** Logging function

```javascript
// Add after DOMContentLoaded, before socket connect
function logTrackingEvent(event_type, data) {
    if (!window.PROFILING_ENABLED) return;

    window.trackingEvents.push({
        ts: new Date().toISOString(),
        event: event_type,
        ...data
    });
}
```

**Änderung 3:** In socket 'data' handler

```javascript
window.socket.on('data', function(data) {
    try {
        // Log player position updates
        if (data.data_type === 'player_position_update' && window.PROFILING_ENABLED) {
            logTrackingEvent("BROWSER_RECEIVED", {
                steamid: data.payload?.steamid
            });
        }

        // ... rest of existing handler code
```

### 9. bot/modules/players/templates/webmap/player_update_handler.html

**Änderung:** Nach marker update

```javascript
// Update or create marker
if (playerMarkers[steamid]) {
    // Update existing marker position
    playerMarkers[steamid].setLatLng([pos.x, pos.z]);

    // Track marker update
    if (window.PROFILING_ENABLED) {
        logTrackingEvent("MARKER_UPDATED", {
            steamid: steamid
        });
    }
} else {
    // ... create new marker code
}
```

---

## Test-Ablauf

1. `PROFILING_ENABLED=True` setzen in run config
2. Bot starten
3. Browser öffnen, auf Webmap gehen
4. Warten bis genau 10 LP commands durchgelaufen sind (30 Sekunden)
5. Browser sendet Tracking-Events zurück zum Server
6. Server schreibt `bot/diagnostic_logs/command_tracking_lp_{timestamp}.json`
7. Datei analysieren - Zeitdifferenzen zwischen Events zeigen wo Delays sind

---

## Gevent-Kompatibilität

- **Kein Threading/Locking** - nur dict operations
- **Kein time.sleep()** - nur timestamps
- **Import tracker nur wenn gebraucht** - `from bot.tracking import tracker` in Funktionen
- Tracker ist singleton, kein shared state außer `_command_to_id` dict (read/write in selben Thread)

---

## Erweiterbarkeit

Andere Commands tracken:
1. `debug_id` in action_meta setzen (z.B. `"debug_id": "teleportplayer"`)
2. Fertig - alle logging points funktionieren automatisch
