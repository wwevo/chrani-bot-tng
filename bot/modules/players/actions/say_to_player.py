from bot import loaded_modules_dict, telnet_prefixes
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 5  # [seconds]
    timeout_start = time()
    event_data[1]["action_identifier"] = action_name

    target_player_steamid = event_data[1].get("steamid", None)
    message = event_data[1].get("message", None)

    # Get player entity ID - game requires entity ID instead of steamid
    dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(dataset, {})
        .get(target_player_steamid, {})
    )
    # Check if player is online before attempting to send message
    if player_dict.get("is_online", False) is False:
        event_data[1]["fail_reason"] = "player is not online"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    player_entity_id = player_dict.get("id")
    if not player_entity_id:
        event_data[1]["fail_reason"] = "player entity ID not found"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    command = "sayplayer {} \"{}\"".format(player_entity_id, message)
    if not module.telnet.add_telnet_command_to_queue(command):
        event_data[1]["fail_reason"] = "duplicate command"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    poll_is_finished = False
    # Modern format: timestamps ARE present in "Executing command" lines
    regex = (
        telnet_prefixes["telnet_log"]["timestamp"] +
        r"Executing\scommand\s\'" + command + r"\'\sby\sTelnet\sfrom\s(?P<called_by>.*)"
    )
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
            poll_is_finished = True

        if match:
            module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "sends a message to any player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
