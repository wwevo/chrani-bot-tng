from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 5  # [seconds]
    timeout_start = time()

    target_player_steamid = event_data[1].get("steamid", None)
    mute_status = event_data[1].get("mute_status", None)

    command = "bc-mute {} {}".format(target_player_steamid, mute_status)
    module.telnet.add_telnet_command_to_queue(command)
    poll_is_finished = False
    regex = (
        r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
        r"INF Executing\scommand\s\'" + command + r"\'\sby\sTelnet\sfrom\s(?P<called_by>.*)"
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
    target_player_steamid = event_data[1].get("steamid", None)
    flag_player_to_be_muted = event_data[1].get("mute_status", None)
    active_dataset = event_data[1].get("dataset", None)

    module.dom.data.upsert({
        "module_players": {
            "elements": {
                active_dataset: {
                    target_player_steamid: {
                        "is_muted": flag_player_to_be_muted
                    }
                }
            }
        }
    })

    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "mutes or unmutes a given player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
