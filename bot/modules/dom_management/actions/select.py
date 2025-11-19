from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    target_module = event_data[1].get("target_module", None)
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    dom_element_select_root = event_data[1].get("dom_element_select_root", ["selected_by"])
    dom_element_origin = event_data[1].get("dom_element_origin", None)
    dom_element_owner = event_data[1].get("dom_element_owner", None)
    dom_element_identifier = event_data[1].get("dom_element_identifier", None)

    if all([
        action is not None,
        dom_element_origin is not None,
        dom_element_owner is not None,
        dom_element_identifier is not None
    ]):
        if action in [  # only proceed with known commands
            "select_dom_element",
            "deselect_dom_element"
        ]:
            general_root = [target_module, "elements", dom_element_origin, dom_element_owner]
            full_root = general_root + dom_element_select_root

            selected_by_dict_element = module.dom_management.get_dict_element_by_path(module.dom.data, full_root)

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
                print(error)

            # Build data payload
            data_payload = {
                "selected_by": selected_by_dict_element,
                "dataset": dom_element_origin,
                "dataset_original": dom_element_origin,
                "owner": dom_element_owner,
                "identifier": dom_element_identifier
            }

            # Build nested structure dynamically based on dom_element_select_root
            # All keys except the last one (which is "selected_by") define nesting levels
            nested_keys = dom_element_select_root[:-1]  # Remove "selected_by"

            # Build nested dict from inside out
            nested_data = data_payload
            for key in reversed(nested_keys):
                nested_data = {key: nested_data}

            module.dom.data.upsert({
                target_module: {
                    "elements": {
                        dom_element_origin: {
                            dom_element_owner: nested_data
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid, min_callback_level=4)

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


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "handles selecting or deselecting an element in the dom for further actions",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
