from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    return

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_to_be_updated_steamid = event_data[1].get("steamid", None)
    permission_level = event_data[1].get("level", 1000)

    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    player_to_be_updated = (
        module.dom.data
        .get("module_players", {})
        .get(active_dataset, {})
        .get("elements", {})
        .get(player_to_be_updated_steamid, None)
    )

    if player_to_be_updated is not None:
        module.dom.data.upsert({
            "module_players": {
                active_dataset: {
                    "elements": {
                        player_to_be_updated_steamid: {
                            "permission_level": permission_level
                        }
                    }
                }
            }
        })

        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return
    else:
        event_data[1]["fail_reason"].append(
            "player does not exist on this server / has not logged in yet t create a file"
        )

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return

def callback_skip(module, action_meta, dispatchers_id=None):
    return

def callback_fail(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "id": action_name,
    "description": "updates a players profiles permission data",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail
    },
    "parameters": {
        "requires_telnet_connection": False,
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
