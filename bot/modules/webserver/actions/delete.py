from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    return

    action = event_data[1].get("action", None)
    target_module = event_data[1].get("target_module", None)
    action_is_confirmed = event_data[1].get("confirmed", "False")
    event_data[1]["action_identifier"] = action_name
    # get active_dataset from somewhere (delete.py)

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
            loaded_modules_dict[target_module].set_current_view(dispatchers_steamid, {
                "current_view": "delete-modal"
            })
            return

    elif action == "cancel_delete_selected_dom_elements":
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return
    target_module = event_data[1].get("target_module", None)
    loaded_modules_dict[target_module].set_current_view(dispatchers_steamid, {
        "current_view": "frontend",
    })


def callback_skip(module, action_meta, dispatchers_id=None):
    return

def callback_fail(module, action_meta, dispatchers_id=None):
    return



action_meta = {
    "description": "tools to help managing dom elements in the webinterface",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
