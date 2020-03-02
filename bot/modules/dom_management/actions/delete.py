from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    target_module = event_data[1].get("target_module", None)
    action_is_confirmed = event_data[1].get("confirmed", "False")

    if action == "delete_selected_dom_elements":
        if action_is_confirmed == "True":
            stuff_to_delete = []
            for path, dom_element_key, dom_element in module.dom.get_dom_element_by_query(
                target_module=target_module,
                query="selected_by"
            ):
                if dispatchers_steamid in dom_element:
                    stuff_to_delete.append([target_module, "elements"] + path)

            for dom_element_to_delete in stuff_to_delete:
                module.dom.data.remove_key_by_path(
                    dom_element_to_delete,
                    dispatchers_steamid=dispatchers_steamid
                )

            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return
        else:
            # show the modal!
            module.dom.data.upsert({
                target_module: {
                    "visibility": {
                        dispatchers_steamid: {
                            "current_view": "modal"
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)

            return
    elif action == "cancel_delete_selected_dom_elements":
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, event_data, dispatchers_steamid, match=None):
    target_module = event_data[1].get("target_module", None)
    module.dom.data.upsert({
        target_module: {
            "visibility": {
                dispatchers_steamid: {
                    "current_view": "frontend"
                }
            }
        }
    }, dispatchers_steamid=dispatchers_steamid)

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
