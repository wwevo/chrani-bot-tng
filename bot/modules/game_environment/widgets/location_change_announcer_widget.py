from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def announce_location_change(*args, **kwargs):
    """
    Handler that announces location edits in the map chat.
    This demonstrates that the callback_dict system works - multiple modules can
    subscribe to the same DOM path changes without modifying the locations module.
    """
    module = args[0]
    method = kwargs.get("method", None)
    updated_values_dict = kwargs.get("updated_values_dict", {})
    matched_path = kwargs.get("matched_path", "")

    # Only announce on update, not insert or remove
    if method != "update":
        return

    # Extract information from the matched path
    # Pattern: module_locations/elements/%map_identifier%/%owner_steamid%/%element_identifier%
    path_parts = matched_path.split("/")
    if len(path_parts) < 5:
        return

    map_identifier = path_parts[2]
    owner_steamid = path_parts[3]
    location_identifier = path_parts[4]

    # Get player name from DOM
    player_name = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(map_identifier, {})
        .get(owner_steamid, {})
        .get("name", "Unknown Player")
    )

    # Get location name from the updated values if available
    location_name = updated_values_dict.get("name", location_identifier)

    # Send chat message via say_to_all
    event_data = ['say_to_all', {
        'message': (
            '[FFAA00]Location Update:[-] {player} edited location [00FFFF]{location}[-]'
            .format(
                player=player_name,
                location=location_name
            )
        )
    }]
    module.trigger_action_hook(module, event_data=event_data)


widget_meta = {
    "description": "Announces location changes in map chat (test for callback_dict system)",
    "main_widget": None,  # No UI widget, just a handler
    "handlers": {
        # Subscribe to location changes - any module can do this!
        "module_locations/elements/%map_identifier%/%owner_steamid%/%element_identifier%": announce_location_change
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
