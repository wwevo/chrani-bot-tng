from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    event_data[1]["action_identifier"] = action_name

    target_player_steamid = event_data[1].get("steamid", None)
    auth_status = event_data[1].get("auth_status", None)
    active_dataset = event_data[1].get("dataset", None)

    if all([target_player_steamid, auth_status is not None, active_dataset]):
        module.dom.data.upsert({
            "module_players": {
                "elements": {
                    active_dataset: {
                        target_player_steamid: {
                            "is_authenticated": auth_status
                        }
                    }
                }
            }
        })
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "toggles a player's authentication status",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
