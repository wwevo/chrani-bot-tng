from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    event_data[1]["action_identifier"] = action_name
    action = event_data[1].get("action", None)
    location_owner = event_data[1].get("dom_element_owner", None)
    location_identifier = event_data[1].get("dom_element_identifier", None)
    location_origin = event_data[1].get("dom_element_origin", None)

    if action == "show_options":
        current_view = "options"
    elif action == "show_frontend":
        current_view = "frontend"
    elif action == "show_create_new":
        current_view = "create_new"
    elif action == "edit_location_entry":
        current_view = "edit_location_entry"
    elif action == "show_special_locations":
        current_view = "special_locations"
    elif action == "show_map":
        current_view = "map"
    else:
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    module.set_current_view(dispatchers_steamid, {
        "current_view": current_view,
        "location_owner": location_owner,
        "location_identifier": location_identifier,
        "location_origin": location_origin
    })
    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages location stuff",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
