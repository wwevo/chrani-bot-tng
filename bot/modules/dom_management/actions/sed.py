from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def get(d, l):
    if len(l) == 1:
        return d.get(l[0], [])
    return get(d.get(l[0], {}), l[1:])


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    target_module = event_data[1].get("target_module", None)
    dom_element_select_root = event_data[1].get("dom_element_select_root", ["selected_by"])
    dom_element_origin = event_data[1].get("dom_element_origin", None)
    dom_element_owner = event_data[1].get("dom_element_owner", None)
    dom_element_identifier = event_data[1].get("dom_element_identifier", None)

    if all([
        action is not None
    ]):
        general_root = ["module_dom", target_module, dom_element_origin, dom_element_owner]
        if action == "select_entry" or action == "deselect_entry":
            full_root = general_root + dom_element_select_root

            selected_by_dict_element = get(module.dom.data, full_root)

            if action == "select_entry":
                selected_by_dict_element.append(dispatchers_steamid)
            elif action == "deselect_entry":
                selected_by_dict_element.remove(dispatchers_steamid)

            current_level = 0
            selected_by_dict = {}
            for key in reversed(dom_element_select_root):
                if current_level == 0:
                    selected_by_dict = {
                        key: selected_by_dict_element,
                        "origin": dom_element_origin,
                        "owner": dom_element_owner,
                        "identifier": dom_element_identifier
                    }
                else:
                    selected_by_dict = {
                        key: selected_by_dict
                    }
                current_level += 1

            module.dom.data.upsert({
                "module_dom": {
                    target_module: {
                        dom_element_origin: {
                            dom_element_owner: selected_by_dict
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid, min_callback_level=4)

            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return

        if action == "enable_location_entry" or action == "disable_location_entry":
            element_is_enabled = True if action == "enable_location_entry" else False

            module.dom.data.upsert({
                "module_locations": {
                    "elements": {
                        dom_element_origin: {
                            dom_element_owner: {
                                dom_element_identifier: {
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
    "description": "tools to help managing dom elements in the webinterface",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
