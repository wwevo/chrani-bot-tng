from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 1.5  # [seconds]
    timeout_start = time()

    module.telnet.add_telnet_command_to_queue("admin list")
    poll_is_finished = False
    regex = (
        r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
        r"INF Executing\scommand\s\'admin list\'\sby\sTelnet\sfrom\s(?P<called_by>.*)\s"
        r"(?P<raw_adminlist>Defined Permissions\:.*\d{17})"
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
    regex = (
        r"(?:^\s{0,7})(?P<level>\d{1,2})\:\s(?P<steamid>\d{17})(?P<name>(?:\s)(?:\()(?:\w+)(?:\)))?"
    )
    raw_adminlist = match.group("raw_adminlist")
    admin_dict = {}
    for m in re.finditer(regex, raw_adminlist, re.MULTILINE):
        admin_dict[m.group("steamid")] = m.group("level")

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "admins": admin_dict
        }
    }, overwrite=True)

    execute_only_once = event_data[1]["execute_only_once"]
    if execute_only_once:
        module.disable_action(action_name)


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "gets a list of all admins and mods",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
