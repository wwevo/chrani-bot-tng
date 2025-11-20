# DOM Helper Migration Plan

## Step 1: Add Helper to Module Base Class

**File:** `bot/module.py`

Add method to Module class:

```python
def get_element_from_callback(self, updated_values_dict, matched_path):
    """
    Get full element from DOM based on callback data.

    Args:
        updated_values_dict: Dict from callback kwargs
        matched_path: Pattern like "module_x/elements/%dataset%/%owner%/%id%"

    Returns:
        Full element dict from DOM
    """
    # Parse matched_path to determine structure
    parts = matched_path.split('/')

    # Standard structure: module/elements/dataset/owner/identifier
    if 'elements' not in parts or len(parts) < 4:
        return {}

    # Get active dataset
    active_dataset = self.dom.data.get("module_game_environment", {}).get("active_dataset")

    # Extract module name from pattern
    module_name = parts[0]

    # Extract keys from updated_values_dict
    # For depth 4: {identifier: {data}}
    # For depth 3: {owner: {identifier: {data}}}

    if len(parts) == 5:  # Depth 4: module/elements/dataset/owner/identifier
        identifier = list(updated_values_dict.keys())[0]
        element_dict = updated_values_dict[identifier]
        owner = element_dict.get("owner")

        # Get from DOM
        return (
            self.dom.data
            .get(module_name, {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(owner, {})
            .get(identifier, {})
        )

    elif len(parts) == 4:  # Depth 3: module/elements/dataset/owner
        owner = list(updated_values_dict.keys())[0]

        # Return all elements for this owner
        return (
            self.dom.data
            .get(module_name, {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(owner, {})
        )

    return {}
```

## Step 2: Update All Handlers

**Pattern to find handlers:**
```bash
grep -r "def.*\*args.*\*\*kwargs" bot/modules/*/widgets/*.py
```

**For each handler, replace:**

```python
# OLD:
def handler(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", {})

    for identifier, data in updated_values_dict.items():
        owner = data.get("owner")
        # ... complex DOM lookups ...
```

```python
# NEW:
def handler(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", {})
    matched_path = kwargs.get("matched_path", "")

    for identifier, data in updated_values_dict.items():
        # Get full element
        element = module.get_element_from_callback(
            {identifier: data},
            matched_path
        )

        # Use element directly
        owner = element.get("owner")
        name = element.get("name")
        # etc.
```

## Step 3: Migration Checklist

Run script to find all handlers:
```bash
python3 scripts/analyze_callback_usage.py
```

Update each file in `CALLBACK_DICT_INVENTORY.md`:

**Locations module:**
- [ ] `manage_locations_widget.py::table_row`
- [ ] `manage_locations_widget.py::update_location_on_map`
- [ ] `manage_locations_widget.py::update_selection_status`
- [ ] `manage_locations_widget.py::update_enabled_flag`
- [ ] `manage_locations_widget.py::update_player_location`

**Players module:**
- [ ] `manage_players_widget.py::table_rows`
- [ ] `manage_players_widget.py::update_widget`
- [ ] `manage_players_widget.py::update_selection_status`
- [ ] `manage_players_widget.py::update_actions_status`

**Game environment:**
- [ ] `gameserver_status_widget.py::update_widget`
- [ ] `gettime_widget.py::update_widget`
- [ ] `manage_entities_widget.py::*` (check all handlers)

**Test handlers:**
- [ ] `location_change_announcer_widget.py::announce_location_change`

## Step 4: Testing

For each updated handler:

```bash
# Start bot
# Trigger handler (edit location, toggle enabled, etc.)
# Check logs for errors
# Verify UI updates correctly
```

## Step 5: Documentation

Create `HANDLER_PATTERN.md`:

```markdown
# Handler Pattern

All handlers use this pattern:

```python
def my_handler(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", {})
    matched_path = kwargs.get("matched_path", "")

    for key, data in updated_values_dict.items():
        # Get full element from DOM
        element = module.get_element_from_callback(
            {key: data},
            matched_path
        )

        # Use element data
        # ...
```

That's it.
```
```

## Automated Validation

```bash
# Check all handlers use the pattern:
grep -A 10 "def.*handler.*args.*kwargs" bot/modules/*/widgets/*.py | \
  grep -L "get_element_from_callback"
# Should return empty
```

## Done

All handlers now consistently get full elements from DOM.
No more guessing what's in `updated_values_dict`.
