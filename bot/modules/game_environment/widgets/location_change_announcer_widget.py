from bot import loaded_modules_dict
from os import path, pardir
from bot.logger import get_logger

logger = get_logger(__name__)

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

    # DEBUG: Log what we received
    logger.info(
        "location_change_debug",
        method=method,
        updated_values_dict_type=type(updated_values_dict).__name__,
        updated_values_dict_repr=repr(updated_values_dict)[:200]
    )

    # Only announce on update, not insert or remove
    if method != "update":
        return

    if not isinstance(updated_values_dict, dict):
        return

    # Get active dataset (map identifier)
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        return

    # updated_values_dict structure at this depth:
    # {owner_steamid: {location_identifier: {location_data}}}
    for owner_steamid, locations in updated_values_dict.items():
        if not isinstance(locations, dict):
            continue

        for location_identifier, location_dict in locations.items():
            if not isinstance(location_dict, dict):
                continue

            # Get player name from DOM
            player_name = (
                module.dom.data
                .get("module_players", {})
                .get("elements", {})
                .get(active_dataset, {})
                .get(owner_steamid, {})
                .get("name", "Unknown Player")
            )

            # Get location name - might not be in updated_values if only is_enabled changed
            # So fall back to reading from DOM
            location_name = location_dict.get("name", None)
            if location_name is None:
                location_name = (
                    module.dom.data
                    .get("module_locations", {})
                    .get("elements", {})
                    .get(active_dataset, {})
                    .get(owner_steamid, {})
                    .get(location_identifier, {})
                    .get("name", location_identifier)
                )

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
