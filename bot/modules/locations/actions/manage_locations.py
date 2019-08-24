from bot import loaded_modules_dict
from os import path, pardir
module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    location_identifier = event_data[1].get("location_identifier", None)
    current_map_identifier = (
        module.dom.data.get("module_environment", {})
        .get("gameprefs", {})
        .get("GameName", None)
    )

    if action == "create_new" or action == "edit":
        location_name = event_data[1].get("location_name", None)
        if location_identifier is None:
            location_identifier = ''.join(e for e in location_name if e.isalnum())
        location_shape = event_data[1].get("location_shape", module.default_options.get("standard_location_shape", None))
        location_coordinates = event_data[1].get("location_coordinates", None)
        location_dimensions = event_data[1].get("location_dimensions", None)
        location_enabled = event_data[1].get("location_enabled", False)
        players_current_locations = (
            module.dom.data.get("module_locations", {})
            .get("elements", {})
            .get(current_map_identifier, {})
            .get(dispatchers_steamid, {})
        )
        if location_identifier in players_current_locations:
            pass

        if all([
            action is not None,
            location_name is not None and len(location_name) >= 3,
            location_identifier is not None,
            location_shape is not None,
            current_map_identifier is not None,
        ]):
            module.dom.data.upsert({
                module.get_module_identifier(): {
                    "elements": {
                        current_map_identifier: {
                            dispatchers_steamid: {
                                location_identifier: {
                                    "name": location_name,
                                    "identifier": location_identifier,
                                    "origin": current_map_identifier,
                                    "shape": location_shape,
                                    "coordinates": location_coordinates,
                                    "dimensions": location_dimensions,
                                    "owner": dispatchers_steamid,
                                    "is_enabled": location_enabled,
                                    "selected_by": []
                                }
                            }
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid, max_callback_level=3)
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return
    elif action == "delete_selected_entries":
        """ remove all locations selected by the current user """
        all_available_locations = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})
        locations_to_remove = []
        for map_identifier, location_owner in all_available_locations.items():
            for owner_steamid, player_locations in location_owner.items():
                for identifier, location_dict in player_locations.items():
                    if dispatchers_steamid in location_dict.get("selected_by"):
                        locations_to_remove.append(
                            (map_identifier, owner_steamid, identifier)
                        )

        for location_tuple in locations_to_remove:
            module.dom.data.remove({
                "module_locations": {
                    "elements": {
                        location_tuple[0]: {
                            location_tuple[1]: location_tuple[2]
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)

        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages location entries",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
