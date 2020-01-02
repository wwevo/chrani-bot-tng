from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    target_module = event_data[1].get("target_module", None)
    dom_element_select_root = event_data[1].get("dom_element_select_root", ["selected_by"])
    dom_element_origin = event_data[1].get("dom_element_origin", None)
    dom_element_owner = event_data[1].get("dom_element_owner", None)
    dom_element_identifier = event_data[1].get("dom_element_identifier", None)

    if action is not None:
        if action == "select_dom_element" or action == "deselect_dom_element":
            general_root = [target_module, "elements", dom_element_origin, dom_element_owner]
            full_root = general_root + dom_element_select_root

            selected_by_dict_element = module.dom_management.get_dict_element_by_path(module.dom.data, full_root)
            try:
                if action == "select_dom_element":
                    if dispatchers_steamid not in selected_by_dict_element:
                        selected_by_dict_element.append(dispatchers_steamid)
                elif action == "deselect_dom_element":
                    if dispatchers_steamid in selected_by_dict_element:
                        selected_by_dict_element.remove(dispatchers_steamid)
            except ValueError as error:
                print(error)

            """ we want to get to the selected_by list, which can be on a different level for each module
            since we store the path to it in the settings, we can simply construct it on the go.
            """
            max_discovered_level = 0
            selected_by_dict = {}
            for path_fragment in reversed(dom_element_select_root):
                if max_discovered_level == 0:
                    selected_by_dict = {
                        path_fragment: selected_by_dict_element,
                        "dataset": dom_element_origin,
                        "owner": dom_element_owner,
                        "identifier": dom_element_identifier
                    }
                else:
                    selected_by_dict = {
                        path_fragment: selected_by_dict
                    }
                max_discovered_level += 1

            """ we do a # + max_discovered_level so we won't trigger actions associated at lower levels
            the 3 in this example translates to "%target_module%/elements/%element_origin%/%dom_element_owner"
            otherwise we'd possibly trigger widget-updates whenever we select something
            """
            module.dom.data.upsert({
                target_module: {
                    "elements": {
                        dom_element_origin: {
                            dom_element_owner: selected_by_dict
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid, min_callback_level=3 + max_discovered_level)

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
