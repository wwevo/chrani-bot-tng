# Callback_Dict Refactoring - Technical Implementation Guide

## The Problem

```python
# edit_location sendet:
{"name": "Lobby", "owner": "12345", "coordinates": {...}, ...}  # ALLES
# Handler bekommt vollständiges Element ✓

# toggle_enabled_flag sendet:
{"is_enabled": True}  # NUR DAS!
# Handler bekommt unvollständiges Element ✗
# Handler MUSS jetzt mühsam owner, name, coordinates etc. aus DOM holen
```

**Result:** Jeder Handler braucht komplizierte DOM-Fallback-Logik. Fehleranfällig und umständlich.

## The Solution

**Enrichment in callback_dict:**
- Wenn `upsert()` partielle Daten bekommt
- Hole aktuelles Element aus DOM
- Merge: `{**dom_element, **partial_update}`
- Handler bekommt IMMER vollständiges Element

**Result:** Handler werden simpel. Kein DOM-Fallback mehr nötig.

---

## Step 1: Find Everything

**Ziel:** Komplette Liste aller betroffenen Stellen.

```bash
cd /home/user/chrani-bot-tng
python3 scripts/analyze_callback_usage.py
```

**Output:** `CALLBACK_DICT_INVENTORY.md` mit allen:
- `upsert()` calls
- `append()` calls
- `remove_key_by_path()` calls
- Handler-Registrierungen

**Check:**
- [ ] Script läuft ohne Fehler
- [ ] Inventory hat alle Module (locations, players, game_environment, ...)
- [ ] Keine Dateien vergessen

---

## Step 2: Implement Enrichment

**File:** `bot/modules/dom/callback_dict.py`

**Add these methods to CallbackDict class:**

```python
def _get_element_at_depth(self, path_components: List[str], target_depth: int) -> dict:
    """
    Get full element at target depth.

    Example: path = ['module_locations', 'elements', 'TestGame', '12345', 'Lobby', 'is_enabled']
             target_depth = 4
             returns: full Lobby location dict
    """
    if len(path_components) < target_depth:
        return {}

    element_path = path_components[:target_depth]
    try:
        return self._get_nested_value(self, element_path) or {}
    except (KeyError, TypeError, IndexError):
        return {}

def _should_enrich(self, path_components: List[str]) -> tuple[bool, int]:
    """
    Determine if enrichment needed and at what depth.

    Rules:
    - Paths with 'elements' at depth 1 → enrich at depth 4 (element level)
    - Others → no enrichment

    Returns: (should_enrich, target_depth)
    """
    if len(path_components) < 2:
        return False, 0

    # Check if this is an element path (e.g., module_x/elements/...)
    if path_components[1] == 'elements':
        return True, 4

    return False, 0

def _enrich_values(self, updates: dict, path_components: List[str]) -> dict:
    """
    Enrich partial update with full element from DOM.

    Args:
        updates: Partial update dict (e.g., {"is_enabled": True})
        path_components: Current path in DOM

    Returns:
        Enriched dict with full element data
    """
    should_enrich, target_depth = self._should_enrich(path_components)

    if not should_enrich:
        return updates

    if not isinstance(updates, dict):
        return updates

    current_depth = len(path_components)

    # Only enrich at or below target depth
    if current_depth < target_depth:
        return updates

    # Get full element from DOM
    full_element = self._get_element_at_depth(path_components, target_depth)

    if not isinstance(full_element, dict):
        return updates

    # Merge: updates override DOM values
    return {**full_element, **updates}
```

**Modify `_upsert_recursive()`:**

Find this section (around line 335):

```python
# Collect callbacks for this change (skip if unchanged)
if method != "unchanged":
    callbacks = self._collect_callbacks(
        path=full_path,
        method=method,
        updated_values=updates,  # ← OLD
        original_values=original_state,
        dispatchers_steamid=dispatchers_steamid,
        min_depth=min_depth,
        max_depth=max_depth
    )
    callbacks_accumulator.extend(callbacks)
```

Replace with:

```python
# Collect callbacks for this change (skip if unchanged)
if method != "unchanged":
    # Enrich updates with full element data
    enriched_updates = self._enrich_values(updates, full_path_components)

    callbacks = self._collect_callbacks(
        path=full_path,
        method=method,
        updated_values=enriched_updates,  # ← NEW: ENRICHED!
        original_values=original_state,
        dispatchers_steamid=dispatchers_steamid,
        min_depth=min_depth,
        max_depth=max_depth
    )
    callbacks_accumulator.extend(callbacks)
```

**Test:**

Create test file `test_enrichment.py`:

```python
from bot.modules.dom.callback_dict import CallbackDict

# Test 1: Partial update gets enriched
cd = CallbackDict()

# Setup: Create full element in DOM
cd.update({
    "module_locations": {
        "elements": {
            "TestGame": {
                "12345": {
                    "Lobby": {
                        "name": "Lobby",
                        "owner": "12345",
                        "coordinates": {"x": 100, "y": 0, "z": 200},
                        "is_enabled": False
                    }
                }
            }
        }
    }
})

# Test: Partial update (only is_enabled)
received_update = None

def test_handler(*args, **kwargs):
    global received_update
    received_update = kwargs.get("updated_values_dict")

cd.register_callback(
    module=None,
    path_pattern="module_locations/elements/TestGame/12345/Lobby",
    callback=test_handler
)

# Trigger partial update
cd.upsert({
    "module_locations": {
        "elements": {
            "TestGame": {
                "12345": {
                    "Lobby": {
                        "is_enabled": True  # Only this field!
                    }
                }
            }
        }
    }
})

# Verify: Handler should receive FULL element
assert received_update is not None, "Handler not called"
assert "name" in received_update, "Missing name (enrichment failed)"
assert "owner" in received_update, "Missing owner (enrichment failed)"
assert "coordinates" in received_update, "Missing coordinates (enrichment failed)"
assert received_update["is_enabled"] == True, "is_enabled not updated"
assert received_update["name"] == "Lobby", "name wrong"
assert received_update["owner"] == "12345", "owner wrong"

print("✅ Enrichment test passed!")
```

Run:
```bash
cd /home/user/chrani-bot-tng
python3 test_enrichment.py
```

**Check:**
- [ ] Test passes
- [ ] No errors in logs
- [ ] Bot still starts without errors

**If test fails:** Revert callback_dict.py and debug.

---

## Step 3: Fix All Upsert Calls

**From inventory:** List all files with `upsert()` calls.

**For each file:**

1. **Analyze:** Does it send complete or partial data?
2. **Add callback levels** if missing:

```python
# Before:
module.dom.data.upsert({...})

# After:
module.dom.data.upsert({...},
    min_callback_level=4,  # Trigger from element level
    max_callback_level=5   # Up to property level
)
```

**Standard levels:**
- Element changes (locations, players): `min=4, max=5`
- Property changes only: `min=4, max=5` (enrichment handles it)
- High-level changes (visibility): `min=2, max=2`

3. **Test file:** Edit location, toggle enabled, etc. Verify handlers work.

**Automated check:**

```bash
# Find all upsert without callback levels:
grep -rn "\.upsert(" bot/modules --include="*.py" | grep -v "min_callback_level"
```

Should return empty list when done.

---

## Step 4: Simplify All Handlers

**From inventory:** List all handler functions.

**For each handler:**

**Remove this pattern:**

```python
# OLD - DELETE THIS:
full_location_dict = (
    module.dom.data
    .get("module_locations", {})
    .get("elements", {})
    .get(active_dataset, {})
    .get(owner_steamid, {})
    .get(identifier, {})
)

coordinates = location_dict.get("coordinates")
if coordinates is None:
    coordinates = full_location_dict.get("coordinates", {})
```

**Replace with:**

```python
# NEW - USE THIS:
# Enrichment guarantees complete element
coordinates = location_dict.get("coordinates", {})
```

**Example - `update_location_on_map` handler:**

Before (lines 862-892 in manage_locations_widget.py):
```python
owner_steamid = location_dict.get("owner")
if owner_steamid is None:
    continue

# Get full location data from DOM if fields are missing
full_location_dict = (...)

coordinates = location_dict.get("coordinates")
if coordinates is None:
    coordinates = full_location_dict.get("coordinates", {})
```

After:
```python
# Trust enrichment - all fields present
owner_steamid = location_dict.get("owner")
if owner_steamid is None:
    continue  # Should never happen now

coordinates = location_dict.get("coordinates", {})
dimensions = location_dict.get("dimensions", {})
# No DOM fallback needed!
```

**Test each handler:** Trigger with partial update (e.g., toggle enabled). Verify:
- No crashes
- No missing field errors in logs
- UI updates correctly

---

## Step 5: Remove Test Code

**Delete:**
- `bot/modules/game_environment/widgets/location_change_announcer_widget.py` (was only test)

**Check logs:** No more `location_change_debug` messages.

---

## Verification Checklist

Run through all major operations:

- [ ] Edit location → browser updates immediately
- [ ] Toggle enabled → browser updates immediately
- [ ] Move location → browser updates immediately
- [ ] Create location → appears on map
- [ ] Delete location → removed from map
- [ ] Multiple browsers → all see updates

**Check logs for errors:**
```bash
# Should see no callback errors
grep -i "callback_execution_failed" logs/*.log
```

---

## If Something Breaks

**Rollback:**

```bash
git checkout HEAD~1 bot/modules/dom/callback_dict.py
# Restart bot
```

**Debug:**
1. Check which handler crashes (see error logs)
2. Add debug logging to enrichment functions
3. Verify element structure in DOM vs expected
4. Fix issue
5. Re-test

---

## What Changed (Summary)

### callback_dict.py:
- Added `_get_element_at_depth()`
- Added `_should_enrich()`
- Added `_enrich_values()`
- Modified `_upsert_recursive()` to enrich before calling handlers

### All actions with upsert:
- Added explicit `min_callback_level` and `max_callback_level`
- Documented why each level chosen

### All handlers:
- Removed DOM fallback logic
- Simplified to directly use `updated_values_dict`
- Added comments: "enrichment guarantees complete element"

---

## For Future Updates

**Adding new action:**
1. Write `upsert()` with callback levels
2. Can send partial data - enrichment handles it
3. Test

**Adding new handler:**
1. Register in `widget_meta["handlers"]`
2. Assume `updated_values_dict` is complete
3. No DOM fallback needed
4. Test

**That's it!**
