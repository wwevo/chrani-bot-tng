from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 3  # give the command 3 seconds to come through
    timeout_start = time()

    module.telnet.add_telnet_command_to_queue("getgamepref")
    regex = (
        r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
        r"INF Executing\scommand\s\'getgamepref\'\sby\sTelnet\sfrom\s(?P<called_by>.*)\s"
        r"(?P<raw_gameprefs>^(GamePref\..*\s)+)"
    )

    match = None
    match_found = False
    poll_is_finished = False
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer, re.MULTILINE):
            poll_is_finished = True
            match_found = True

    if match_found:
        regex = (
            r"GamePref\.(?P<gamepref_name>.*)\s\=\s(?P<gamepref_value>.*)\s"
        )
        raw_gamestats = match.group("raw_gameprefs")
        gamestats_dict = {}
        all_required_settings_are_available = False
        for m in re.finditer(regex, raw_gamestats, re.MULTILINE):
            stripped_gameprefs = m.group("gamepref_value").rstrip()
            if all([
                m.group("gamepref_name") == "GameName" and len(stripped_gameprefs) >= 1
            ]):
                all_required_settings_are_available = True

            gamestats_dict[m.group("gamepref_name")] = stripped_gameprefs

        module.dom.data.upsert({
            module.get_module_identifier(): {
                "gameprefs": gamestats_dict
            }
        }, overwrite=True)

        if all_required_settings_are_available is True:
            disable_after_success = event_data[1]["disable_after_success"]
            if disable_after_success:
                module.disable_action(action_name)

            module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
            return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    print("working with the \"{}\" dataset".format(module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName", None)))


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "gets a list of all current game-preferences",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
