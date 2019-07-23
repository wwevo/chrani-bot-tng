from bot import loaded_modules_dict
from os import path, pardir
from builtins import int

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    location_name = event_data[1].get("location_name", None)
    location_identifier = event_data[1].get("location_identifier", None)
    location_shape = event_data[1].get("location_shape", None)
    location_coordinates = event_data[1].get("location_coordinates", None)
    location_dimensions = event_data[1].get("location_dimensions", None)
    current_map_identifier = module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName", None)

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
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    module.dom.data.upsert({
        module.get_module_identifier(): {
            "locations": {
                dispatchers_steamid: {
                    event_data[1].get("location_identifier"): {
                        "name": event_data[1].get("location_name"),
                        "identifier": event_data[1].get("location_identifier"),
                        "origin": module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName"),
                        "shape": event_data[1].get("location_shape"),
                        "coordinates": event_data[1].get("location_coordinates"),
                        "dimensions": event_data[1].get("location_dimensions"),
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
