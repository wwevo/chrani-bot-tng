from bot import loaded_modules_dict
from os import path, pardir
module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    location_identifier = event_data[1].get("location_identifier", None)
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    location_owner = dispatchers_steamid if action == "create_new" else event_data[1].get("location_owner", dispatchers_steamid)
    location_name = event_data[1].get("location_name", None)
    if location_identifier is None:
        location_identifier = ''.join(e for e in location_name if e.isalnum())
    location_shape = event_data[1].get("location_shape", module.default_options.get("standard_location_shape", None))
    location_types = event_data[1].get("location_type", [])
    location_coordinates = event_data[1].get("location_coordinates", {})
    location_teleport_entry = event_data[1].get("location_teleport_entry", {})
    location_dimensions = event_data[1].get("location_dimensions", {})
    location_enabled = event_data[1].get("is_enabled", False)
    last_changed = event_data[1].get("last_changed", False)

    if all([
        action is not None,
        location_name is not None and len(location_name) >= 3,
        location_identifier is not None,
        location_shape is not None,
        active_dataset is not None
    ]):
        module.dom.data.upsert({
            module.get_module_identifier(): {
                "elements": {
                    active_dataset: {
                        str(location_owner): {
                            location_identifier: {
                                "name": location_name,
                                "identifier": location_identifier,
                                "dataset": active_dataset,
                                "shape": location_shape,
                                "type": location_types,
                                "coordinates": location_coordinates,
                                "teleport_entry": location_teleport_entry,
                                "dimensions": location_dimensions,
                                "owner": str(location_owner),
                                "is_enabled": location_enabled,
                                "selected_by": [],
                                "last_changed": last_changed
                            }
                        }
                    }
                }
            }
        }, dispatchers_steamid=dispatchers_steamid, max_callback_level=3)
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
