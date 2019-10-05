from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 5  # [seconds]
    timeout_start = time()

    player_to_be_teleported = event_data[1].get("steamid", None)
    coordinates = event_data[1].get("coordinates", None)
    reason = event_data[1].get("reason", None)

    if coordinates is not None:
        command = "tele {} {} {} {}".format(player_to_be_teleported, coordinates["x"], coordinates["y"], coordinates["z"])
        module.telnet.add_telnet_command_to_queue(command)
        poll_is_finished = False
        regex = (
            r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
            r"INF Executing\scommand\s\'" + command + "\'\sby\sTelnet\sfrom\s(?P<called_by>.*)"
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
    "description": "teleports a player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
