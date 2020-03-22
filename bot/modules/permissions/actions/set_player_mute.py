from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    event_data[1]["action_identifier"] = action_name
    player_steamid = event_data[1].get("player_steamid", None)
    active_dataset = event_data[1].get("dataset", None)
    flag_player_to_be_muted = event_data[1].get("is_muted", None)

    if all([
        active_dataset is not None,
        player_steamid is not None,
        flag_player_to_be_muted is not None,
    ]):
        player_dict = (
            module.dom.data
            .get("module_players", {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(player_steamid, {})
        )
        player_is_currently_muted = player_dict.get("is_muted", False)

        if not flag_player_to_be_muted:
            default_player_password = module.default_options.get("default_player_password", None)
            if player_is_currently_muted or default_player_password is None:
                module.callback_success(callback_success, module, event_data, dispatchers_steamid)

            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_steamid = event_data[1].get("player_steamid", None)
    active_dataset = event_data[1].get("dataset", None)

    if player_steamid is not None:
        default_player_password = module.default_options.get("default_player_password", None)
        if default_player_password is not None:
            event_data = ['say_to_player', {
                'steamid': player_steamid,
                'message': '[66FF66]Free speech[-][FFFFFF], you may now chat. Say hello ^^[-]'
            }]
            module.trigger_action_hook(module.players, event_data=event_data)

        event_data = ['toggle_player_mute', {
            'steamid': player_steamid,
            'mute_status': False,
            'dataset': active_dataset
        }]
        module.trigger_action_hook(module.players, event_data=event_data)


def callback_fail(module, event_data, dispatchers_steamid):
    player_steamid = event_data[1].get("player_steamid", None)
    active_dataset = event_data[1].get("dataset", None)

    if player_steamid is not None:
        default_player_password = module.default_options.get("default_player_password", None)
        if default_player_password is not None:
            event_data = ['say_to_player', {
                'steamid': player_steamid,
                'message': '[FF6666]You have been automatically muted[-][FFFFFF], until you have authenticated![-]'
            }]
            module.trigger_action_hook(module.players, event_data=event_data)

        event_data = ['toggle_player_mute', {
            'steamid': player_steamid,
            'mute_status': True,
            'dataset': active_dataset
        }]
        module.trigger_action_hook(module.players, event_data=event_data)


action_meta = {
    "description": "tools to help managing a players ability to chat (and speak?)",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
