from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_VERY_SHORT, TELNET_PREFIXES
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    return

    timeout = TELNET_TIMEOUT_VERY_SHORT
    timeout_start = time()
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    if module.telnet.add_telnet_command_to_queue("admin list"):
        poll_is_finished = False
        regex = action_meta.get("regex")[0]

        while not poll_is_finished and (time() < timeout_start + timeout):
            sleep(0.25)
            match = False
            for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
                poll_is_finished = True

            if match:
                module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
                return

        event_data[1]["fail_reason"].append("action timed out")
    else:
        event_data[1]["fail_reason"].append("action already queued up")

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return

    regex = action_meta.get("regex")[1]
    raw_adminlist = match.group("raw_adminlist")
    admin_dict = {}
    for m in re.finditer(regex, raw_adminlist, re.MULTILINE):
        admin_dict[m.group("steamid")] = m.group("level")

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "admins": admin_dict
        }
    })

    disable_after_success = event_data[1]["disable_after_success"]
    if disable_after_success:
        module.disable_action(action_name)


def callback_skip(module, action_meta, dispatchers_id=None):
    pass

def callback_fail(module, action_meta, dispatchers_id=None):
    pass


action_meta = {
    "id": action_name,
    "description": "gets the current admin-list",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail
    },
    "parameters": {
        "periodic": True,
        "enabled": True,
        "disable_after_success": True,
        "requires_telnet_connection": True,
    },
    "regex": [
        (
            TELNET_PREFIXES["telnet_log"]["timestamp"] +
            r"Executing\scommand\s\'admin list\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
            r"(?P<raw_adminlist>Defined User Permissions:[\s\S]*?(?=Defined Group Permissions:))"
        ),
        (
            r"(?:^\s{0,7})(?P<level>\d{1,2})\:\s+Steam_(?P<steamid>\d{17})"
        )
    ]

}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
