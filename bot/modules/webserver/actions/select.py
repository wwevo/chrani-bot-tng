from pprint import pp

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
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    dom_element_select_root = event_data[1].get("dom_element_select_root", ["selected_by"])
    dataset = event_data[1].get("dataset", None)
    owner_id = event_data[1].get("owner_id", None)
    identifier = event_data[1].get("identifier", None)

    pp(event_data)
    if all([
        action is not None,
        dataset is not None,
        owner_id is not None,
        identifier is not None
    ]):
        if action in [  # only proceed with known commands
            "select_dom_element",
            "deselect_dom_element"
        ]:
            general_root = [target_module, dataset, "elements", owner_id]

            full_root = general_root + dom_element_select_root
            selected_by_dict_element = module.webserver.get_dict_element_by_path(module.dom.data, full_root)

            # CRITICAL: Make a COPY of the list! Otherwise we modify the original list,
            # and then upsert sees old_value == new_value (both are references to the same list)
            # This would cause the callback to NOT fire because method="unchanged"
            selected_by_dict_element = list(selected_by_dict_element)

            try:
                if action == "select_dom_element":
                    if dispatchers_steamid not in selected_by_dict_element:
                        selected_by_dict_element.append(dispatchers_steamid)
                elif action == "deselect_dom_element":
                    if dispatchers_steamid in selected_by_dict_element:
                        selected_by_dict_element.remove(dispatchers_steamid)
            except ValueError as error:
                print("select_list_manipulation_failed")

            # Build data payload
            data_payload= {
                target_module: {
                    dataset: {
                        "elements": {
                            owner_id: {
                                "selected_by": selected_by_dict_element,
                                "dataset": dataset,
                                "owner": owner_id,
                                "identifier": identifier,
                                "debug": True
                            }
                        }
                    }
                }
            }

            module.dom.data.upsert(data_payload, dispatchers_steamid=dispatchers_steamid)
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return

        else:
            event_data[1]["fail_reason"].append("unknown action")
    else:
        event_data[1]["fail_reason"].append("required options not set")

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


""" these will not be called directly. Always call the modules_callback and that will call this local function:
module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
"""
def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return

def callback_skip(module, action_meta, dispatchers_id=None):
    return

def callback_fail(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "id": action_name,
    "description": "handles selecting or deselecting an element in the dom for further actions",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_fail": callback_fail
    },
    "parameters": {
        "periodic": False,
        "requires_telnet_connection": True,
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
