from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    player_steamid = event_data[1].get("player_steamid", None)
    dataset = event_data[1].get("dataset", None)
    is_muted = event_data[1].get("is_muted", None)

    if all([
        action is not None and action == "set mute status",
        dataset is not None,
        player_steamid is not None,
        is_muted is not None,
    ]):
        module.dom.data.upsert({
            "module_players": {
                "elements": {
                    dataset: {
                        player_steamid: {
                            "is_muted": is_muted
                        }
                    }
                }
            }
        })

        if not is_muted:
            module.callback_success(callback_success, module, event_data, dispatchers_steamid)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[66FF66]Free speech[-][FFFFFF], you may now chat. Say hello ^^[-]'
        }]
        module.trigger_action_hook(module.players, event_data, player_steamid)

        event_data = ['toggle_player_mute', {
            'steamid': player_steamid,
            'mute_status': False
        }]
        module.trigger_action_hook(module.players, event_data, player_steamid)


def callback_fail(module, event_data, dispatchers_steamid):
    player_steamid = event_data[1].get("player_steamid", None)
    if player_steamid is not None:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FF6666]You have been automatically muted[-][FFFFFF], until you have authenticated![-]'
        }]
        module.trigger_action_hook(module.players, event_data, player_steamid)

        event_data = ['toggle_player_mute', {
            'steamid': player_steamid,
            'mute_status': True
        }]
        module.trigger_action_hook(module.players, event_data, player_steamid)


action_meta = {
    "description": "tools to help managing a players ability to chat (and speak?)",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
