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

**Critical Logging Points:**
- [ ] Telnet command failed
- [ ] Parse error
- [ ] Timeout
- [ ] Unexpected response

## Logging Requirements

### What to Log

**ERRORS (Always):**
- Action failures (validation, execution)
- Network errors (telnet, HTTP, socket.io)
- Parse errors (malformed data)
- DOM operation failures
- Missing/invalid configuration

**WARNINGS (Always):**
- Deprecated usage
- Fallback behavior
- Rate limiting
- Auth issues (retry-able)

**INFO (Startup only):**
- Module loaded
- Server started
- Connected to game server

**DEBUG (Opt-in via config):**
- Action execution trace
- DOM operations
- Socket events
- Data transformations

### What NOT to Log

- Successful operations (checkbox clicked, tile loaded)
- Regular polling (ding/dong success)
- Normal data flow
- Redundant state changes

## Proposed Log Format

### Python Backend Format
```
[LEVEL] [TIMESTAMP] event_name | context_key=value context_key=value
```

**Example:**
```
[ERROR] [2025-01-19 12:34:56.123] tile_fetch_failed | user=steamid123 z=4 x=-2 y=1 status=404 url=http://...
[WARN]  [2025-01-19 12:34:57.456] auth_missing_sid | user=steamid456 action=tile_request
[INFO]  [2025-01-19 12:00:00.000] module_loaded | module=webserver version=1.0
```

**Benefits:**
- Grep-able: `grep "user=steamid123"`
- Human-readable
- Timestamp for correlation
- Structured key=value pairs

### JavaScript Frontend Format
```
[PREFIX] event_name | context
```

**Example:**
```
[SOCKET ERROR] event_processing_failed | data_type=widget_content error=Cannot read property 'id' of undefined
[MAP ERROR] shape_creation_failed | location_id=map_owner_loc1 shape=circle error=Invalid radius
```

**Ding/Dong:** Only log if latency > 5000ms or timeout

## Implementation Plan

### Phase 1: Foundation (Priority 1)
- [ ] Create `bot/logger.py` with ContextLogger class
- [ ] Define log levels and configuration
- [ ] Add correlation ID system (optional, for tracing request chains)

### Phase 2: Critical Error Paths (Priority 1)
- [ ] Webserver: Login, tile proxy, socket events
- [ ] DOM Management: Select, delete, upsert failures
- [ ] Telnet: Command failures, timeouts
- [ ] Actions: All user-triggered action errors

### Phase 3: JavaScript Cleanup (Priority 1)
- [ ] Ding/Dong: Only log slow/failed
- [ ] Socket events: Only errors (keep debug mode)
- [ ] Map: Only errors during shape creation

### Phase 4: Startup Info (Priority 2)
- [ ] Module loading
- [ ] Configuration summary
- [ ] Game server connection status

### Phase 5: Debug Mode (Priority 3)
- [ ] Opt-in verbose logging
- [ ] Action traces
- [ ] Data flow tracking

## File-by-File Logging Audit

### High Priority Files
1. `bot/modules/webserver/__init__.py` - 20+ print statements
2. `bot/modules/dom_management/actions/select.py` - Error handling
3. `bot/modules/telnet/__init__.py` - Connection/command errors
4. `bot/modules/webserver/static/system.js` - Socket event handler
5. `bot/modules/locations/templates/*/view_map.html` - Map errors

### Medium Priority Files
6. All action files in `bot/modules/*/actions/*.py`
7. All trigger files in `bot/modules/*/triggers/*.py`
8. Widget files with event handling

### Low Priority Files
9. Static utility functions
10. Template rendering (already has good error handling via try-catch)

## Success Criteria

After implementation, troubleshooting should be:
1. **Grep for user:** `grep "user=steamid123" logs/app.log`
2. **See exact error:** `grep "ERROR" logs/app.log`
3. **Trace action flow:** Correlation IDs link related events
4. **Minimal noise:** No success spam, only problems
5. **Human readable:** Can understand what happened without decoding

## Next Steps

1. Review and approve this plan
2. Create `bot/logger.py` with basic ContextLogger
3. Update 3-5 critical files as proof of concept
4. Test and refine format
5. Systematically update remaining files
6. Document logging conventions for future development
