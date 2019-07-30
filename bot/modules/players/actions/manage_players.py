from bot import loaded_modules_dict
from os import path, pardir
from builtins import int

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)

    if action in [
        "select_player_entry",
        "deselect_player_entry",
        "delete_selected_entries"
    ]:
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    action = event_data[1].get("action", None)
    player_steamid = event_data[1].get("steamid", None)

    selected_players = module.dom.data.get("module_players", {}).get("selected", {}).get(dispatchers_steamid, []).copy()
    if action == "select_player_entry":
        selected_players.append(player_steamid)
        module.dom.data.upsert({
            "module_players": {
                "selected": {
                    dispatchers_steamid: selected_players
                }
            }
        }, dispatchers_steamid=dispatchers_steamid)
    elif action == "deselect_player_entry":
        selected_players.remove(player_steamid)
        module.dom.data.upsert({
            "module_players": {
                "selected": {
                    dispatchers_steamid: selected_players
                }
            }
        }, dispatchers_steamid=dispatchers_steamid)
    elif action == "delete_selected_entries":
        if len(selected_players) >= 1:
            """ deletion stuff will go here! """

            module.dom.data.upsert({
                "module_players": {
                    "selected": {
                        dispatchers_steamid: []
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages player entries",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
