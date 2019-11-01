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

    print(target_module, "shall", action, "for", dispatchers_steamid)

    if all([
        action is not None
    ]):
        general_root = ["module_dom", target_module]
        owner_root = [dom_element_origin, dom_element_owner]
        if action == "select_dom_element" or action == "deselect_dom_element":
            full_root = general_root + owner_root + dom_element_select_root
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
            }, dispatchers_steamid=dispatchers_steamid, min_callback_level=3 + current_level)

            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return
        elif action == "delete_selected_dom_elements":
            all_available_elements = (
                module.dom.data
                .get("module_dom", {})
                .get(target_module, {})
            )

            for selected_by_dict_element in module.dom_management.occurrences_of_key_in_nested_mapping("selected_by", all_available_elements):
                print(selected_by_dict_element)

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
