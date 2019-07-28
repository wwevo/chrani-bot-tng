from bot import loaded_modules_dict
from os import path, pardir
from builtins import int

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    location_identifier = event_data[1].get("location_identifier", None)
    current_map_identifier = module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName", None)

    selected_locations = module.dom.data.get("module_locations", {}).get("selected", {}).get(dispatchers_steamid, []).copy()

    if action == "create_new":
        location_name = event_data[1].get("location_name", None)
        location_shape = event_data[1].get("location_shape", None)
        location_coordinates = event_data[1].get("location_coordinates", None)
        location_dimensions = event_data[1].get("location_dimensions", None)

        if all([
            action is not None,
            location_name is not None and len(location_name) >= 5,
            location_identifier is not None,
            location_shape is not None,
            location_coordinates is not None,
            location_dimensions is not None,
            current_map_identifier is not None,
        ]) and all([
            int(location_coordinates["x"]) != 0,
            int(location_coordinates["y"]) != 0,
            int(location_coordinates["z"]) != 0
        ]):
            module.dom.data.upsert({
                module.get_module_identifier(): {
                    "locations": {
                        dispatchers_steamid: {
                            location_identifier: {
                                "name": location_name,
                                "identifier": location_identifier,
                                "origin": current_map_identifier,
                                "shape": location_shape,
                                "coordinates": location_coordinates,
                                "dimensions": location_dimensions,
                                "owner": dispatchers_steamid,
                                "is_enabled": True
                            }
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)

            module.dom.data.upsert({
                module.get_module_identifier(): {
                    "visibility": {
                        dispatchers_steamid: {
                            "current_view": "frontend",
                            "current_view_steamid": None
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return
    elif action == "select_location_entry" or action == "deselect_location_entry":
        if action == "select_location_entry":
            selected_locations.append(location_identifier)
            module.dom.data.upsert({
                "module_locations": {
                    "selected": {
                        dispatchers_steamid: selected_locations
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)
        elif action == "deselect_location_entry":
            selected_locations.remove(location_identifier)
            module.dom.data.upsert({
                "module_locations": {
                    "selected": {
                        dispatchers_steamid: selected_locations
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)

        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return
    elif action == "delete_selected_entries" and len(selected_locations) >= 1:
        print(selected_locations)
        module.dom.data.upsert({
            "module_locations": {
                "selected": {
                    dispatchers_steamid: []
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
