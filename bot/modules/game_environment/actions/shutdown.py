from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    timeout = 10

    if not module.telnet.add_telnet_command_to_queue("shutdown"):
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    poll_is_finished = False
    regex = (
        r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
        r"INF Disconnect.*"
    )

    timeout_start = time()
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.5)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer):
            poll_is_finished = True

        if match:
            module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    module.dom.data.upsert({
        "module_game_environment": {
            active_dataset: {
                "cancel_shutdown": False,
                "shutdown_in_seconds": None,
                "force_shutdown": False
            }
        }
    })


def callback_fail(module, event_data, dispatchers_steamid):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    module.dom.data.upsert({
        "module_game_environment": {
            active_dataset: {
                "cancel_shutdown": False,
                "shutdown_in_seconds": None,
                "force_shutdown": False
            }
        }
    })


action_meta = {
    "description": "Cleanly shuts down the server",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
