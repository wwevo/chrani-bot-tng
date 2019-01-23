from modules import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid, **kwargs):
    timeout = 3  # [seconds]
    timeout_start = time()

    module.telnet.add_telnet_command_to_queue("gettime")
    poll_is_finished = False
    while not poll_is_finished and (time() < timeout_start + timeout):
        match = False
        for match in re.finditer(r"Day\s(\d{1,5}),\s(\d{1,2}):(\d{1,2}).*", module.telnet.telnet_buffer):
            poll_is_finished = True

        if match:
            callback_success(module, event_data, dispatchers_steamid, match, **kwargs)
            return
        sleep(0.5)

    callback_fail(module, event_data, dispatchers_steamid, **kwargs)


def callback_success(module, event_data, dispatchers_steamid, match, **kwargs):
    print(match)
    module.webserver.send_data_to_client(
        event_data=match.group(0),
        data_type="alert_message",
        clients=[dispatchers_steamid]
    )
    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid, **kwargs):
    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "gets the current gettime readout",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
