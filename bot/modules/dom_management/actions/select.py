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

    # DEBUG: Log incoming request
    print(f"[DEBUG SELECT] Action: {action}, Module: {target_module}")
    print(f"[DEBUG SELECT] Origin: {dom_element_origin}, Owner: {dom_element_owner}, ID: {dom_element_identifier}")
    print(f"[DEBUG SELECT] Select root: {dom_element_select_root}")

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

            # DEBUG: Log path construction
            print(f"[DEBUG SELECT] Full path: {full_root}")

            selected_by_dict_element = module.dom_management.get_dict_element_by_path(module.dom.data, full_root)

            # DEBUG: Log lookup result
            print(f"[DEBUG SELECT] Found selected_by list: {selected_by_dict_element}")
            print(f"[DEBUG SELECT] Type: {type(selected_by_dict_element)}")

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
                if max_discovered_level == 0:  # the first level will get metadata
                    selected_by_dict = {
                        path_fragment: selected_by_dict_element,
                        "dataset": dom_element_origin,
                        "dataset_original": dom_element_origin,  # Store original for callbacks
                        "owner": dom_element_owner,
                        "identifier": dom_element_identifier
                    }
                else:
                    selected_by_dict = {
                        path_fragment: selected_by_dict
                    }
                max_discovered_level += 1

            """ we do a min_callback_level at # + max_discovered_level so we won't trigger actions associated at lower
            levels. the 3 in this case translates to
                "%target_module%(0)/elements(1)/%element_origin%(2)/%dom_element_owner(3)"
                
            This way we will only trigger on changes from dom_element_owner and deeper, which is what we want.
            I'm sure with better design this could be done automatically, feel free to contribute if you know how :)
            """
            # DEBUG: Log upsert operation
            print(f"[DEBUG SELECT] Calling upsert with min_callback_level: {4 + max_discovered_level}")
            print(f"[DEBUG SELECT] Updated selected_by list: {selected_by_dict_element}")

            # Build the full path to selected_by to trigger the right callback level
            # Start with innermost dict and wrap outwards: owner -> origin -> elements -> module
            upsert_dict = selected_by_dict
            for path_elem in [dom_element_owner, dom_element_origin, "elements", target_module]:
                upsert_dict = {path_elem: upsert_dict}

            print(f"[DEBUG SELECT] Upsert structure (first 200 chars): {str(upsert_dict)[:200]}")

            module.dom.data.upsert(
                upsert_dict,
                dispatchers_steamid=dispatchers_steamid,
                min_callback_level=4 + max_discovered_level
            )

            print(f"[DEBUG SELECT] Upsert completed, calling callback_success")
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return

        else:
            print(f"[DEBUG SELECT] FAIL: Unknown action: {action}")
            event_data[1]["fail_reason"].append("unknown action")
    else:
        print(f"[DEBUG SELECT] FAIL: Required options not set")
        print(f"[DEBUG SELECT] Action: {action}, Origin: {dom_element_origin}, Owner: {dom_element_owner}, ID: {dom_element_identifier}")
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
