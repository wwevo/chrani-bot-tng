from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    location_origin = event_data[1].get("location_origin", None)
    location_owner = event_data[1].get("location_owner", None)
    location_identifier = event_data[1].get("location_identifier", None)

    element_is_selected_by = (
        module.dom.data.get(module.get_module_identifier(), {})
        .get("elements", {})
        .get(location_origin, {})
        .get(location_owner, {})
        .get(location_identifier, {})
        .get("selected_by", [])
    )

    if all([
        location_origin is not None,
        location_owner is not None,
        location_identifier is not None,
    ]):
        if action == "select_location_entry" or action == "deselect_location_entry":
            if action == "select_location_entry":
                element_is_selected_by.append(dispatchers_steamid)
            elif action == "deselect_location_entry":
                element_is_selected_by.remove(dispatchers_steamid)

            module.dom.data.upsert({
                "module_locations": {
                    "elements": {
                        location_origin: {
                            location_owner: {
                                location_identifier: {
                                    "selected_by": element_is_selected_by
                                }
                            }
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid, min_callback_level=5)

            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return

        if action == "enable_location_entry" or action == "disable_location_entry":
            element_is_enabled = True if action == "enable_location_entry" else False

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

            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "tools to help managing locations in the webinterface",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
