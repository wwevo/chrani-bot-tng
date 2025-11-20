# Logging System Analysis & Plan

## System Architecture Overview

```
Browser (JavaScript)
    ↕ Socket.io
Python Backend (Flask + Socket.io)
    ↕ Telnet
7D2D Game Server
```

## Current Logging State

### Python Backend
- **Format:** Inconsistent mix of:
  - `print(f"[PREFIX] message")`
  - `print("{}: message".format(module))`
  - Plain `print("message")`
- **No:**
  - Timestamps
  - Log levels (ERROR, WARN, INFO, DEBUG)
  - User context
  - Correlation IDs
  - Structured data

### JavaScript Frontend
- **Issues:**
  - Ding/Dong logs every 10 seconds (spam)
  - Many debug messages that don't help troubleshooting
  - No structured logging
  - Success messages mixed with errors

## Event Flow Analysis

### 1. User Action Flow
```
User clicks checkbox (Browser)
  → Widget event sent via Socket.io
    → Python: webserver receives event
      → Python: Action handler (e.g., dom_management/select)
        → Python: DOM upsert
          → Python: Callback triggers
            → Python: Widget handler updates
              → Socket.io sends update back
                → Browser: DOM updated
```

**Critical Logging Points:**
- [ ] Action received (user, action, data)
- [ ] Action validation failed
- [ ] DOM operation (path, method, user)
- [ ] Callback trigger (which handler, why)
- [ ] Socket send (to whom, what type)

### 2. Tile Request Flow
```
Browser requests tile (HTTP GET)
  → Python: webserver /map_tiles route
    → Python: Auth check
      → Python: Proxy to game server
        → 7D2D: Returns tile OR error
          → Python: Forward response OR error
            → Browser: Displays tile OR 404
```

**Critical Logging Points:**
- [ ] Tile request (only on ERROR)
- [ ] Auth failure
- [ ] Game server error (status code, url)
- [ ] Network timeout

### 3. Telnet Command Flow
```
Python: Action needs game data
  → Python: Telnet send command
    → 7D2D: Processes command
      → 7D2D: Returns response
        → Python: Parse response
          → Python: Update DOM
            → Python: Trigger callbacks
```

## Log Format
### Python Backend Format
```
[LEVEL] [TIMESTAMP] event_name | context_key=value context_key=value
```

**Example:**
```
[ERROR] [2025-01-19 12:34:56.123] tile_fetch_failed | user=steamid123 z=4 x=-2 y=1 status=404 url=http://...
[WARN ]  [2025-01-19 12:34:57.456] auth_missing_sid | user=steamid456 action=tile_request
[INFO ]  [2025-01-19 12:00:00.000] module_loaded | module=webserver version=1.0
```

### JavaScript Frontend Format
```
[PREFIX] event_name | context
```

**Example:**
```
[SOCKET ERROR] event_processing_failed | data_type=widget_content error=Cannot read property 'id' of undefined
[MAP ERROR   ] shape_creation_failed | location_id=map_owner_loc1 shape=circle error=Invalid radius
```
