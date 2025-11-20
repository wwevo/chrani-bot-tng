# Callback_Dict System Refactoring Plan

## Executive Summary

**Problem:** Das callback_dict System ist inkonsistent. Handler bekommen manchmal vollständige Elemente (z.B. von `edit_location`), manchmal nur geänderte Felder (z.B. von `toggle_enabled_flag`). Dies zwingt Handler zu komplexen DOM-Fallback-Logiken.

**Lösung:** Callback_dict automatisch "enrichment" - sendet immer vollständige Elemente an Handler, indem es partielle Updates mit aktuellen DOM-Daten merged.

**Vorteile:**
- ✅ Handler werden einfacher (kein DOM-Fallback nötig)
- ✅ Konsistentes Verhalten system-weit
- ✅ Bessere Performance (weniger DOM-Lookups in Handlern)
- ✅ Klarere Semantik: `updated_values_dict` = vollständiger Zustand NACH Update
- ✅ Klarere Semantik: `original_values_dict` = vollständiger Zustand VOR Update

---

## Current State Analysis

### Problem Examples

**Beispiel 1: edit_location (funktioniert)**
```python
# bot/modules/locations/actions/edit_location.py
module.dom.data.upsert({
    "module_locations": {
        "elements": {
            active_dataset: {
                location_owner: {
                    location_identifier: {
                        "name": "...",
                        "owner": "...",
                        "coordinates": {...},
                        "dimensions": {...},
                        "teleport_entry": {...},
                        "is_enabled": True,
                        # ... ALLE Felder!
                    }
                }
            }
        }
    }
}, max_callback_level=4)
```

Handler bekommt vollständiges Element ✓

**Beispiel 2: toggle_enabled_flag (Problem!)**
```python
# bot/modules/locations/actions/toggle_enabled_flag.py
module.dom.data.upsert({
    "module_locations": {
        "elements": {
            location_origin: {
                location_owner: {
                    location_identifier: {
                        "is_enabled": True  # NUR dieses Feld!
                    }
                }
            }
        }
    }
}, min_callback_level=4)
```

Handler bekommt unvollständiges Element ✗
→ Handler muss DOM auslesen um `owner`, `name`, `coordinates` etc. zu bekommen

### All Affected Files (Discovered in Analysis)

#### Actions with upsert() calls:
```
bot/modules/locations/actions/edit_location.py              ✓ Complete element
bot/modules/locations/actions/toggle_enabled_flag.py        ✗ Partial element (is_enabled only)
bot/modules/players/actions/getplayers.py                   ? Unknown (batch update)
bot/modules/players/actions/update_player_permission_level.py  ✗ Partial (permission_level only)
bot/modules/players/actions/toggle_player_mute.py           ✗ Partial (is_muted only)
bot/modules/players/actions/playerspawn.py                  ? Unknown
bot/modules/game_environment/actions/gettime.py             N/A (depth 2, no elements)
bot/modules/game_environment/actions/getgamestats.py        N/A (depth 2, no elements)
bot/modules/game_environment/actions/getgameprefs.py        N/A (depth 2, no elements)
bot/modules/dom_management/actions/select.py                ✗ Partial (selected_by only)
```

**IMPORTANT:** Need to scan ALL modules for additional upsert calls!

#### Widgets with handlers:
```
bot/modules/locations/widgets/manage_locations_widget.py
  - select_view (depth 2)
  - table_row (depth 3)
  - update_location_on_map (depth 4) ← FIXED manually with DOM fallback
  - update_selection_status (depth 5)
  - update_enabled_flag (depth 5) ← Uses original_values_dict workaround
  - update_player_location (cross-module, depth 4)

bot/modules/players/widgets/manage_players_widget.py
  - select_view (depth 2)
  - table_rows (depth 3)
  - update_widget (depth 4)
  - update_selection_status (depth 5)
  - update_actions_status (depth 4)

bot/modules/game_environment/widgets/gameserver_status_widget.py
  - update_widget (depths 1-2)

bot/modules/game_environment/widgets/gettime_widget.py
  - update_widget (depth 2)

bot/modules/game_environment/widgets/manage_entities_widget.py
  - [Need to analyze]

bot/modules/game_environment/widgets/location_change_announcer_widget.py
  - announce_location_change (depth 4) ← TEST handler, needs owner field
```

**IMPORTANT:** Need to scan ALL modules for additional handlers!

---

## Implementation Strategy

### Phase 0: Discovery & Inventory (MUST DO FIRST!)

**Goal:** Find EVERY upsert call and handler registration in the codebase.

**Tasks:**
1. Scan all modules for `dom.data.upsert(` calls
2. Scan all modules for `widget_meta["handlers"]` registrations
3. Scan all modules for `dom.data.append(` calls
4. Scan all modules for `dom.data.remove_key_by_path(` calls
5. Document each one with:
   - File path
   - Line number
   - Depth of data change
   - Whether it sends complete or partial data
   - Which handlers will be triggered
   - Whether handler needs changes

**Output:** Complete inventory in `CALLBACK_DICT_INVENTORY.md`

**Estimated Time:** 2-3 hours (can be automated with grep/analysis tools)

---

### Phase 1: Implement Enrichment in callback_dict

**Goal:** Modify `CallbackDict` to automatically enrich partial updates with full element data from DOM.

**Files to modify:**
- `bot/modules/dom/callback_dict.py`

**Changes:**

```python
# In CallbackDict class

def _get_element_at_depth(self, path_components, target_depth):
    """
    Get the full element at a specific depth in the path.

    For example, if path is ['module_locations', 'elements', 'TestGame', '12345', 'Lobby', 'is_enabled']
    and target_depth is 4, return the full 'Lobby' location dict.
    """
    if len(path_components) < target_depth:
        return {}

    element_path = path_components[:target_depth]
    try:
        return self._get_nested_value(self, element_path)
    except (KeyError, TypeError):
        return {}

def _enrich_updated_values(self, updated_values, path_components, current_depth, target_depth):
    """
    Enrich updated_values with full element data from DOM.

    Args:
        updated_values: The partial update dict (e.g., {"is_enabled": True})
        path_components: Current path in DOM
        current_depth: Current depth in recursion
        target_depth: Depth where we want full element

    Returns:
        Enriched dict with full element data merged with updates
    """
    if current_depth != target_depth:
        return updated_values

    if not isinstance(updated_values, dict):
        return updated_values

    # Get full element from current DOM state
    full_element = self._get_element_at_depth(path_components, target_depth)

    if not isinstance(full_element, dict):
        return updated_values

    # Merge: updated values override DOM values
    # Use copy to avoid modifying original
    enriched = {**full_element, **updated_values}

    return enriched

def _upsert_recursive(
    self,
    current_dict: dict,
    updates: Dict,
    original_state: Dict,
    path_components: List[str],
    callbacks_accumulator: List[Dict],
    dispatchers_steamid: Optional[str],
    min_depth: int,
    max_depth: int
) -> None:
    """Recursive helper for upsert operation."""
    current_depth = len(path_components)

    for key, new_value in updates.items():
        # Build the full path for this key
        full_path_components = path_components + [key]
        full_path = self._join_path(full_path_components)

        # Determine the operation type
        key_exists = key in current_dict
        old_value = current_dict.get(key)

        if key_exists:
            # Update case
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                # Both are dicts - recurse deeper
                method = "update"
                self._upsert_recursive(
                    current_dict=current_dict[key],
                    updates=new_value,
                    original_state=original_state.get(key, {}),
                    path_components=full_path_components,
                    callbacks_accumulator=callbacks_accumulator,
                    dispatchers_steamid=dispatchers_steamid,
                    min_depth=min_depth,
                    max_depth=max_depth
                )
            elif old_value == new_value:
                # Value unchanged - skip callbacks
                method = "unchanged"
            else:
                # Value changed - update it
                method = "update"
                current_dict[key] = new_value
        else:
            # Insert case
            method = "insert"
            current_dict[key] = new_value

            # If inserted value is a dict, recurse through it
            if isinstance(new_value, dict):
                self._upsert_recursive(
                    current_dict=current_dict[key],
                    updates=new_value,
                    original_state={},
                    path_components=full_path_components,
                    callbacks_accumulator=callbacks_accumulator,
                    dispatchers_steamid=dispatchers_steamid,
                    min_depth=min_depth,
                    max_depth=max_depth
                )

        # Collect callbacks for this change (skip if unchanged)
        if method != "unchanged":
            # **NEW: Enrich updated values before sending to callbacks**
            callback_depth = len(full_path_components)

            # Determine element depth from path structure
            # Standard structure: module_name/category/dataset/owner/identifier/properties...
            # Element depth is typically 4 (identifier level)
            # This should be configurable or detected automatically
            element_depth = 4  # TODO: Make this smarter or configurable

            enriched_updates = updates
            if callback_depth >= element_depth and isinstance(updates, dict):
                enriched_updates = self._enrich_updated_values(
                    updated_values=updates,
                    path_components=full_path_components,
                    current_depth=callback_depth,
                    target_depth=element_depth
                )

            callbacks = self._collect_callbacks(
                path=full_path,
                method=method,
                updated_values=enriched_updates,  # ← ENRICHED!
                original_values=original_state,
                dispatchers_steamid=dispatchers_steamid,
                min_depth=min_depth,
                max_depth=max_depth
            )
            callbacks_accumulator.extend(callbacks)
```

**Testing Strategy:**
1. Unit tests for `_get_element_at_depth()`
2. Unit tests for `_enrich_updated_values()`
3. Integration test: upsert partial data, verify handler receives full element
4. Regression test: upsert full data, verify no changes

**Rollback Plan:**
Keep original callback_dict.py as callback_dict.py.backup
If issues arise, can quickly revert

**Estimated Time:** 4-6 hours including tests

---

### Phase 2: Standardize Callback Levels

**Goal:** Add explicit callback levels to ALL upsert calls.

**Convention:**
```python
# For element-level changes (depth 4):
module.dom.data.upsert({...}, min_callback_level=4, max_callback_level=4)

# For property-level changes (depth 5+):
module.dom.data.upsert({...}, min_callback_level=4, max_callback_level=None)

# The enrichment ensures handlers get full element even at depth 5+
```

**Files to modify:** (from Phase 0 inventory)
- Every action file with upsert() calls
- Document WHY each level is chosen (comment in code)

**Template for changes:**
```python
# BEFORE:
module.dom.data.upsert({
    "module_locations": {
        "elements": {
            location_origin: {
                location_owner: {
                    location_identifier: {
                        "is_enabled": element_is_enabled
                    }
                }
            }
        }
    }
}, dispatchers_steamid=dispatchers_steamid, min_callback_level=5)

# AFTER:
module.dom.data.upsert({
    "module_locations": {
        "elements": {
            location_origin: {
                location_owner: {
                    location_identifier: {
                        "is_enabled": element_is_enabled
                    }
                }
            }
        }
    }
}, dispatchers_steamid=dispatchers_steamid,
   min_callback_level=4,  # Trigger from element level down
   max_callback_level=5)  # Trigger up to property level
   # Enrichment ensures handlers at depth 4 get full element despite partial update
```

**Testing Strategy:**
- For each changed file, test that:
  1. Correct handlers are triggered
  2. Handlers receive expected data structure
  3. UI updates correctly

**Estimated Time:** 6-8 hours (depends on number of files)

---

### Phase 3: Simplify All Handlers

**Goal:** Remove DOM fallback logic from handlers since enrichment guarantees full elements.

**Pattern to remove:**
```python
# OLD PATTERN (remove this):
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

```python
# NEW PATTERN (use this):
# Just trust that updated_values_dict is complete!
coordinates = location_dict.get("coordinates", {})
```

**Files to modify:** (from Phase 0 inventory)
- Every handler function in every widget file
- Document the assumption: "enrichment guarantees complete element"

**Testing Strategy:**
- For each handler:
  1. Trigger with partial update (e.g., toggle is_enabled)
  2. Verify handler doesn't crash
  3. Verify handler produces correct output
  4. Verify no errors in logs about missing fields

**Estimated Time:** 8-10 hours (many handlers to update)

---

### Phase 4: Documentation & Conventions

**Goal:** Document the new system for future developers.

**Deliverables:**

1. **CALLBACK_DICT_GUIDE.md**
   - How callback_dict works
   - Enrichment explanation
   - When to use which callback levels
   - Handler signature convention
   - Examples

2. **Code comments in callback_dict.py**
   - Explain enrichment
   - Explain depth conventions
   - Link to guide

3. **Developer checklist**
   - When adding new action: checklist of what to do
   - When adding new handler: checklist of what to do

**Estimated Time:** 2-3 hours

---

### Phase 5: Cleanup & Optimization

**Goal:** Remove test code, optimize performance.

**Tasks:**
1. Remove `location_change_announcer_widget.py` (was only a test)
2. Profile callback_dict performance
3. Consider caching for element lookups during enrichment
4. Add performance metrics logging

**Estimated Time:** 3-4 hours

---

## Testing Strategy

### Unit Tests
- Test enrichment logic in isolation
- Test depth detection
- Test merge logic (updated overrides original)

### Integration Tests
- Test complete flows:
  1. Edit location → verify browser updates
  2. Toggle enabled → verify browser updates
  3. Move location → verify browser updates
  4. Create location → verify browser updates
  5. Delete location → verify browser updates

### Regression Tests
- Run existing tests
- Verify no breakage in:
  - Player management
  - Game environment widgets
  - DOM management

### Performance Tests
- Measure callback execution time before/after
- Verify enrichment doesn't cause significant slowdown
- Target: <10ms additional latency per callback

---

## Rollback Strategy

### At Each Phase:
1. Create git branch for phase work
2. Commit after each file change
3. If issues arise:
   - Identify failing component
   - Revert specific commits
   - Fix issue
   - Re-apply changes

### Full Rollback:
If entire refactor needs to be rolled back:
1. Revert callback_dict.py to backup
2. Revert all handler changes
3. Revert all action changes
4. System returns to current working state

**Backup procedure:**
```bash
# Before starting Phase 1:
cp bot/modules/dom/callback_dict.py bot/modules/dom/callback_dict.py.PRE_REFACTOR
git tag pre-callback-refactor
```

---

## Risk Assessment

### High Risk
- **Callback_dict enrichment bugs:** Could break all handlers
  - *Mitigation:* Extensive unit tests, gradual rollout

- **Performance degradation:** Enrichment adds DOM lookups
  - *Mitigation:* Profile first, add caching if needed

### Medium Risk
- **Missing upsert calls in Phase 0:** Could miss files
  - *Mitigation:* Use automated tools (grep, AST analysis)

- **Handler assumptions:** Some handlers might expect partial data
  - *Mitigation:* Review each handler, test thoroughly

### Low Risk
- **Documentation incomplete:** Devs confused later
  - *Mitigation:* Pair programming reviews, examples

---

## Success Criteria

### Phase 1 Success:
- [ ] Unit tests pass for enrichment functions
- [ ] Integration test: partial update triggers handler with full element
- [ ] No regressions in existing functionality

### Phase 2 Success:
- [ ] All upsert calls have explicit callback levels
- [ ] All actions tested and working

### Phase 3 Success:
- [ ] All handlers simplified (no DOM fallback code)
- [ ] All handlers tested and working
- [ ] Browser updates work for all operations

### Phase 4 Success:
- [ ] Documentation complete
- [ ] New developer can understand system from docs

### Overall Success:
- [ ] System-wide consistency in callback behavior
- [ ] Handlers are simpler and more maintainable
- [ ] No functional regressions
- [ ] Performance is acceptable (<10ms added latency)
- [ ] Future developers can easily work with system

---

## Timeline Estimate

| Phase | Description | Estimated Time |
|-------|-------------|----------------|
| 0 | Discovery & Inventory | 2-3 hours |
| 1 | Implement Enrichment | 4-6 hours |
| 2 | Standardize Callback Levels | 6-8 hours |
| 3 | Simplify Handlers | 8-10 hours |
| 4 | Documentation | 2-3 hours |
| 5 | Cleanup & Optimization | 3-4 hours |
| **Total** | | **25-34 hours** |

**Realistic Timeline:** 4-5 working days for single developer

---

## Next Steps for Future Claude

1. **Read this plan completely**
2. **Start with Phase 0** - build complete inventory
3. **Get user approval** on Phase 0 results before proceeding
4. **Implement Phase 1** - this is the core change
5. **Test Phase 1 thoroughly** before proceeding
6. **Proceed phase by phase** - don't skip ahead
7. **Commit frequently** with descriptive messages
8. **If stuck:** ask user for clarification, don't guess

---

## Questions for User (Before Starting)

1. **Scope:** Should this refactor include ALL modules, or only locations/players/game_environment?

2. **Testing:** Do you have automated tests, or will testing be manual?

3. **Timeline:** How urgent is this? Can it be done over multiple sessions?

4. **Backwards Compatibility:** Do you need to support old handler code during transition?

5. **Performance:** What's acceptable latency for callbacks? Current target: <10ms

---

## Appendix A: Depth Convention

Standard DOM structure:
```
Depth 0: module_name          (e.g., "module_locations")
Depth 1: category             (e.g., "elements", "visibility")
Depth 2: dataset              (e.g., "TestGame", active_dataset)
Depth 3: owner/steamid        (e.g., "76561198012345678")
Depth 4: element_identifier   (e.g., "Lobby", "MyBase") ← ELEMENT LEVEL
Depth 5+: properties          (e.g., "is_enabled", "coordinates", "x")
```

**Element Depth = 4** for most cases (locations, players)

Enrichment should target depth 4 to ensure handlers get full elements.

---

## Appendix B: Handler Signature Convention

```python
def my_handler(*args, **kwargs):
    """
    Handler for [describe what this handles].

    Receives enriched data - updated_values_dict is guaranteed to be complete element.
    """
    module = args[0]

    # Method indicates type of change
    method = kwargs.get("method")  # "insert", "update", "remove"

    # Updated values - COMPLETE element after update (enriched by callback_dict)
    updated_values_dict = kwargs.get("updated_values_dict")

    # Original values - COMPLETE element before update
    original_values_dict = kwargs.get("original_values_dict")

    # Dispatcher who triggered the change
    dispatchers_steamid = kwargs.get("dispatchers_steamid")

    # Matched path pattern (contains wildcards like %steamid%)
    matched_path = kwargs.get("matched_path")

    # Example: Check if specific field changed
    if method == "update":
        old_enabled = original_values_dict.get("is_enabled", False)
        new_enabled = updated_values_dict.get("is_enabled", False)

        if old_enabled != new_enabled:
            # is_enabled changed - do something
            pass

    # Access element data directly (no DOM fallback needed!)
    element_name = updated_values_dict.get("name", "Unknown")
    element_owner = updated_values_dict.get("owner", "Unknown")
    coordinates = updated_values_dict.get("coordinates", {})

    # ... handler logic ...
```

---

*End of Plan*
