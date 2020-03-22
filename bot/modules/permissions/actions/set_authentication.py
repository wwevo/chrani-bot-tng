from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
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
                "elements": {
                    dataset: {
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


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[66FF66]Thank you for playing along[-][FFFFFF], you may now leave the Lobby-area[-]'
        }]
        module.trigger_action_hook(module.players, event_data=event_data)


def callback_fail(module, event_data, dispatchers_steamid):
    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FF6666]Could not authenticate[-][FFFFFF], wrong password perhaps?[-]'
        }]
        module.trigger_action_hook(module.players, event_data=event_data)
    pass


action_meta = {
    "description": "sets a players authenticated flag",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
