from bot import loaded_modules_dict
from os import path, pardir
from time import time, sleep
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)

    if action in [
        "kick player"
    ]:
        if action == "kick player":
            timeout = 5  # [seconds]
            timeout_start = time()

            player_to_be_kicked = event_data[1].get("steamid", None)
            reason = event_data[1].get("reason", (
                "no reason provided, "
                "try again in a few minutes and check if perhaps a bloodmoon is in progress ^^ "
                "or something ^^"
            ))

            command = "kick {} \"{}\"".format(player_to_be_kicked, reason)
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
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages player-centered actions: kicking, banning, muting",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
