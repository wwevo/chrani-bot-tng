from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    player_steamid = event_data[1].get("steamid", None)

    selected_players = module.dom.data.get("module_whitelist", {}).get("selected", {}).get(dispatchers_steamid, []).copy()
    if action is not None and player_steamid is not None:
        if len(player_steamid) == 17 and player_steamid.isdigit():
            if action == "select_whitelist_entry":
                selected_players.append(player_steamid)
                module.dom.data.upsert({
                    "module_whitelist": {
                        "selected": {
                            dispatchers_steamid: selected_players
                        }
                    }
                }, dispatchers_steamid=dispatchers_steamid)
            elif action == "deselect_whitelist_entry":
                selected_players.remove(player_steamid)
                module.dom.data.upsert({
                    "module_whitelist": {
                        "selected": {
                            dispatchers_steamid: selected_players
                        }
                    }
                }, dispatchers_steamid=dispatchers_steamid)
            elif action == "add_to_whitelist" or action == "remove_from_whitelist":
                module.dom.data.upsert({
                    "module_whitelist": {
                        "players": {
                            player_steamid: {
                                "on_whitelist": True if action == "add_to_whitelist" else False
                            }
                        }
                    }
                })
                module.dom.data.upsert({
                    "module_whitelist": {
                        "visibility": {
                            dispatchers_steamid: {
                                "current_view": "frontend",
                                "current_view_steamid": None
                            }
                        }
                    }
                }, dispatchers_steamid=dispatchers_steamid)

            else:
                module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
                return

            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return
    elif action is not None and player_steamid is None:
        if action == "activate_whitelist":
            module.dom.data.upsert({
                "module_whitelist": {
                    "is_active": True
                }
            })
        elif action == "deactivate_whitelist":
            module.dom.data.upsert({
                "module_whitelist": {
                    "is_active": False
                }
            })
        elif action == "delete_selected_entries":
            pass
        else:
            module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
            return

        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages whitelist entries",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
