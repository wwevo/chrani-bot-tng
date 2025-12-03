from bot import loaded_modules_dict
from bot.constants import TELNET_PREFIXES
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)
        return

    return

    # NOTE: This action needs event_data from browser which isn't passed correctly yet
    # Keeping old structure but with ticket system for when it's enabled

    timeout = 5  # [seconds]
    action_meta["action_identifier"] = action_name

    target_player_steamid = action_meta.get("steamid", None)
    message = action_meta.get("message", None)

    # Get player entity ID - game requires entity ID instead of steamid
    dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_dict = (
        module.dom.data
        .get("module_players", {})
        .get(dataset, {})
        .get("elements", {})
        .get(target_player_steamid, {})
    )
    # Check if player is online before attempting to send message
    if player_dict.get("is_online", False) is False:
        action_meta["fail_reason"] = "player is not online"
        module.callback_fail(callback_fail, action_meta, dispatchers_id)
        return

    player_entity_id = player_dict.get("id")
    if not player_entity_id:
        action_meta["fail_reason"] = "player entity ID not found"
        module.callback_fail(callback_fail, action_meta, dispatchers_id)
        return

    command = "sayplayer {} \"{}\"".format(player_entity_id, message)

    # NEW: Send command with ticket system
    regex = (
        TELNET_PREFIXES["telnet_log"]["timestamp"] +
        r"Executing\scommand\s\'" + command + r"\'\sby\sTelnet\sfrom\s(?P<called_by>.*)"
    )
    ticket = module.telnet.send_command(command, regex, timeout=timeout)
    result = ticket.wait()

    if result['success']:
        module.callback_success(callback_success, action_meta, dispatchers_id, result['match'])
    else:
        print(f"[say_to_player] Action timeout. Buffer received:\n{result['buffer']}")
        module.callback_fail(callback_fail, action_meta, dispatchers_id)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return


def callback_skip(module, action_meta, dispatchers_id=None):
    return


def callback_fail(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "id": action_name,
    "description": "sends a message to any player",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail
    },
    "parameters": {
        "requires_telnet_connection": True,
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
