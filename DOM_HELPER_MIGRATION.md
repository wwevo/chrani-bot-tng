# DOM Helper Migration Plan

## Step 1: Add Helpers to Module Base Class

**File:** `bot/module.py`

Add two methods to Module class:

```python
def get_element_from_dom(self, module_name, dataset, owner, identifier=None):
    """
    Get full element from DOM.

    Args:
        module_name: e.g. "module_locations"
        dataset: active dataset name
        owner: owner steamid
        identifier: element identifier (optional for owner-level access)

    Returns:
        Full element dict from DOM
    """
    path_data = (
        self.dom.data
        .get(module_name, {})
        .get("elements", {})
        .get(dataset, {})
        .get(owner, {})
    )

    if identifier:
        return path_data.get(identifier, {})

    return path_data


def update_element(self, module_name, dataset, owner, identifier, updates, dispatchers_steamid=None):
    """
    Update element fields in DOM.

    Args:
        module_name: e.g. "module_locations"
        dataset: active dataset name
        owner: owner steamid
        identifier: element identifier
        updates: dict with fields to update
        dispatchers_steamid: who triggered update

    Example:
        module.update_element("module_locations", dataset, owner, "Lobby",
                            {"is_enabled": True})
    """
    # Get current element
    element = self.get_element_from_dom(module_name, dataset, owner, identifier)

    # Merge updates
    element.update(updates)

    # Write back full element
    self.dom.data.upsert({
        module_name: {
            "elements": {
                dataset: {
                    owner: {
                        identifier: element
                    }
                }
            }
        }
    }, dispatchers_steamid=dispatchers_steamid, min_callback_level=4, max_callback_level=5)


def get_element_from_callback(self, updated_values_dict, matched_path):
    """
    Get full element from DOM based on callback data.

    Args:
        updated_values_dict: Dict from callback kwargs
        matched_path: Pattern like "module_x/elements/%dataset%/%owner%/%id%"

    Returns:
        Full element dict from DOM
    """
    parts = matched_path.split('/')

    if 'elements' not in parts or len(parts) < 4:
        return {}

    active_dataset = self.dom.data.get("module_game_environment", {}).get("active_dataset")
    module_name = parts[0]

    # Depth 4: {identifier: {data}}
    if len(parts) == 5:
        identifier = list(updated_values_dict.keys())[0]
        element_dict = updated_values_dict[identifier]
        owner = element_dict.get("owner")

        return self.get_element_from_dom(module_name, active_dataset, owner, identifier)

    # Depth 3: {owner: {...}}
    elif len(parts) == 4:
        owner = list(updated_values_dict.keys())[0]
        return self.get_element_from_dom(module_name, active_dataset, owner)

    return {}
```

## Step 2: Update All Actions

**Find all actions:**
```bash
grep -r "module.dom.data.upsert" bot/modules/*/actions/*.py
```

**Pattern - OLD:**
```python
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
}, dispatchers_steamid=dispatchers_steamid, min_callback_level=4)
```

**Pattern - NEW:**
```python
active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset")

module.update_element(
    "module_locations",
    active_dataset,
    location_owner,
    location_identifier,
    {"is_enabled": element_is_enabled},
    dispatchers_steamid=dispatchers_steamid
)
```

**Actions checklist:**
- [ ] `locations/actions/toggle_enabled_flag.py`
- [ ] `locations/actions/edit_location.py` (keep as-is, already writes full element)
- [ ] `players/actions/update_player_permission_level.py`
- [ ] `players/actions/toggle_player_mute.py`
- [ ] `dom_management/actions/select.py`
- [ ] All other actions with partial upserts

## Step 3: Update All Handlers

**Find all handlers:**
```bash
python3 scripts/analyze_callback_usage.py
```

**Pattern - OLD:**
```python
def handler(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", {})

    for identifier, data in updated_values_dict.items():
        owner = data.get("owner")
        # Complex DOM lookups...
        full_element = module.dom.data.get(...)...
```

**Pattern - NEW:**
```python
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

        # Use directly
        owner = element.get("owner")
        name = element.get("name")
        # ...
```

**Handlers checklist:**
- [ ] `locations/widgets/manage_locations_widget.py::table_row`
- [ ] `locations/widgets/manage_locations_widget.py::update_location_on_map`
- [ ] `locations/widgets/manage_locations_widget.py::update_selection_status`
- [ ] `locations/widgets/manage_locations_widget.py::update_enabled_flag`
- [ ] `players/widgets/manage_players_widget.py::table_rows`
- [ ] `players/widgets/manage_players_widget.py::update_widget`
- [ ] `game_environment/widgets/location_change_announcer_widget.py::announce_location_change`

## Step 4: Testing

**For each file:**
1. Update code
2. Restart bot
3. Trigger action/handler
4. Check logs for errors
5. Verify UI updates

**Automated check:**
```bash
# No more complex upserts:
grep -r "\"elements\":" bot/modules/*/actions/*.py | wc -l
# Should be 0 or very few (only edit_location type actions)

# No more DOM fallback in handlers:
grep -r "\.get.*\.get.*\.get.*\.get" bot/modules/*/widgets/*.py | wc -l
# Should be much lower
```

## Step 5: Example for Future

**New trigger - warn player on low health:**

```python
def low_health_warning(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", {})
    matched_path = kwargs.get("matched_path", "")

    # Get full player element
    for steamid, data in updated_values_dict.items():
        player = module.get_element_from_callback(
            {steamid: data},
            matched_path
        )

        # Check health
        if player.get("health", 100) < 60:
            module.trigger_action_hook(module, event_data=[
                'say_to_player',
                {'steamid': steamid, 'message': 'Low health!'}
            ])

# Register:
widget_meta = {
    "handlers": {
        "module_players/elements/%dataset%/%steamid%": low_health_warning
    }
}
```

**New action - set player flag:**

```python
def main_function(module, event_data, dispatchers_steamid):
    steamid = event_data[1].get("steamid")
    flag_value = event_data[1].get("flag_value")

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset")

    # Update element
    module.update_element(
        "module_players",
        active_dataset,
        steamid,
        None,  # player has no sub-identifier
        {"custom_flag": flag_value},
        dispatchers_steamid=dispatchers_steamid
    )
```

Done. Clear pattern for everything.
