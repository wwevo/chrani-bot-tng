from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    player_steamid = event_data[1].get("player_steamid", None)
    dataset = event_data[1].get("dataset", None)
    entered_password = event_data[1].get("entered_password", False)

    if module.default_options.get("player_password", None) == entered_password:
        is_authenticated = True
    else:
        is_authenticated = False

    if all([
        dataset is not None,
        player_steamid is not None,
        action is not None
    ]):
        if action == "add authentication":
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
            })

    if is_authenticated is True:
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
    else:
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[66FF66]Thank you for playing along[-][FFFFFF], you may now leave the Crater[-]'
        }]
        module.trigger_action_hook(module.players, event_data, player_steamid)


def callback_fail(module, event_data, dispatchers_steamid):
    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FF6666]Something went wrong there[-][FFFFFF], wrong password perhaps?[-]'
        }]
        module.trigger_action_hook(module.players, event_data, player_steamid)
    pass


action_meta = {
    "description": "tools to help managing permissions",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
