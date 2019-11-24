from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 3  # [seconds]
    timeout_start = time()

    module.telnet.add_telnet_command_to_queue("gettime")
    poll_is_finished = False
    regex = (
        r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
        r"Day\s(?P<day>\d{1,5}),\s(?P<hour>\d{1,2}):(?P<minute>\d{1,2}).*"
    )
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer):
            poll_is_finished = True

        if match:
            module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    current_game_name = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get("current_game_name", None)
    )

    # we can't save the gamestats without knowing the game-name, as each game can have different stats.
    if current_game_name is None:
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            current_game_name: {
                "last_recorded_gametime": {
                    "day": match.group("day"),
                    "hour": match.group("hour"),
                    "minute": match.group("minute")
                }
            }
        }
    })


def callback_fail(module, event_data, dispatchers_steamid):
    pass


def skip_it(module, event_data, dispatchers_steamid=None):
    pass


action_meta = {
    "description": "gets the current gettime readout",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "skip_it": skip_it,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
