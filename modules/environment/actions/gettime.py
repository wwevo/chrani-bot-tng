from modules import loaded_modules_dict
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
            telnet_datetime = match.group("datetime")
            poll_is_finished = True

        if match:
            callback_success(module, event_data, dispatchers_steamid, match, telnet_datetime)
            return

    callback_fail(module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match, telnet_datetime):
    if any([
        match.group("day") != module.dom.data.get(module.get_module_identifier(), {}).get("last_recorded_gametime", {}).get("day", 0),
        match.group("hour") != module.dom.data.get(module.get_module_identifier(), {}).get("last_recorded_gametime", {}).get("hour", 0),
        match.group("minute") != module.dom.data.get(module.get_module_identifier(), {}).get("last_recorded_gametime", {}).get("minute", 0)
    ]):
        module.dom.upsert({
            module.get_module_identifier(): {
                "last_recorded_gametime": {
                    "day": match.group("day"),
                    "hour": match.group("hour"),
                    "minute": match.group("minute")
                }
            }
        }, telnet_datetime=telnet_datetime)
        module.update_gametime_widget_frontend()
        module.emit_event_status(event_data, dispatchers_steamid, "success")
    else:
        print("date didn't change since last poll")


def callback_fail(module, event_data, dispatchers_steamid):
    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "gets the current gettime readout",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
