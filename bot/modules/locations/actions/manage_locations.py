from bot import loaded_modules_dict
from os import path, pardir
from builtins import int

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    location_identifier = event_data[1].get("location_identifier", None)
    location_owner = event_data[1].get("location_owner", None)
    current_map_identifier = module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName", None)

    selected_locations = module.dom.data.get("module_locations", {}).get("selected", {}).get(dispatchers_steamid, []).copy()

    if action == "create_new":
        location_name = event_data[1].get("location_name", None)
        location_shape = event_data[1].get("location_shape", None)
        location_coordinates = event_data[1].get("location_coordinates", None)
        location_dimensions = event_data[1].get("location_dimensions", None)
        players_current_locations = module.dom.data.get("module_locations", {}).get("locations", {}).get(dispatchers_steamid, {})

        if all([
            action is not None,
            location_name is not None and len(location_name) >= 4,
            location_identifier is not None and location_identifier not in players_current_locations,
            location_shape is not None,
            location_coordinates is not None,
            location_dimensions is not None,
            current_map_identifier is not None,
        ]) and any([
            int(location_coordinates["x"]) != 0,
            int(location_coordinates["y"]) != 0,
            int(location_coordinates["z"]) != 0
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
                                    "is_enabled": True,
                                    "selected_by": []
                                }
                            }
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid, depth=4)
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return
    elif action == "delete_selected_entries":
        if len(selected_locations) >= 1:
            """ remove all locations selected by the current user """
            for location_identifier in selected_locations:
                module.dom.data.remove({
                    "module_locations": {
                        "elements": {
                            current_map_identifier: {
                                dispatchers_steamid: location_identifier
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
