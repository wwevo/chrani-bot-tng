from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    event_data[1]["action_identifier"] = action_name
    pattern_id = event_data[1].get("pattern_id", None)
    is_selected = event_data[1].get("is_selected", False)

    if pattern_id is not None:
        # Update the pattern's selection state in DOM
        module.dom.data.upsert({
            "module_game_environment": {
                "unmatched_patterns": {
                    pattern_id: {
                        "is_selected": is_selected
                    }
                }
            }
        }, dispatchers_steamid=dispatchers_steamid, min_callback_level=3)

        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "Toggles the selection state of an unmatched telnet pattern",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
