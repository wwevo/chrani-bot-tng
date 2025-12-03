from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    return

    event_data[1]["action_identifier"] = action_name
    player_steamid = event_data[1].get("player_steamid", None)
    dataset = event_data[1].get("dataset", None)
    entered_password = event_data[1].get("entered_password", None)
    default_player_password = module.default_options.get("default_player_password", None)

    if all([
        dataset is not None,
        player_steamid is not None,
        entered_password is not None,
        default_player_password is not None
    ]):
        if default_player_password == entered_password:
            is_authenticated = True
        else:
            is_authenticated = False

        module.dom.data.upsert({
            "module_players": {
                dataset: {
                    "elements": {
                        player_steamid: {
                            "is_authenticated": is_authenticated
                        }
                    }
                }
            }
        }, dispatchers_steamid=player_steamid)

        if is_authenticated is True:
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return

    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[66FF66]Thank you for playing along[-][FFFFFF], you may now leave the Lobby-area[-]'
        }]
        module.trigger_action_hook(module.players, event_data=event_data)


def callback_skip(module, action_meta, dispatchers_id=None):
    return


def callback_fail(module, action_meta, dispatchers_id=None):
    return

    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FF6666]Could not authenticate[-][FFFFFF], wrong password perhaps?[-]'
        }]
        module.trigger_action_hook(module.players, event_data=event_data)
    pass


action_meta = {
    "id": action_name,
    "description": "sets a players authenticated flag",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail,
    },
    "parameters": {
        "requires_telnet_connection": False,
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
