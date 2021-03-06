from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    event_data[1]["action_identifier"] = action_name
    action = event_data[1].get("action", None)
    location_origin = event_data[1].get("dom_element_origin", None)
    location_owner = event_data[1].get("dom_element_owner", None)
    location_identifier = event_data[1].get("dom_element_identifier", None)

    if all([
        action is not None
    ]):
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
    "description": "Sets or removes the enabled flag of a location",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
