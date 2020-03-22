from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    event_data[1]["action_identifier"] = action_name
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_to_be_updated_steamid = event_data[1].get("steamid", None)
    permission_level = event_data[1].get("level", 1000)

    player_to_be_updated = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(player_to_be_updated_steamid, None)
    )

    if player_to_be_updated is not None:
        permission_level_to_update = {
            "permission_level": permission_level
        }
        module.dom.data.upsert({
            "module_players": {
                "elements": {
                    active_dataset: {
                        player_to_be_updated_steamid: permission_level_to_update
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
    "description": "updates a players profiles permission data",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
