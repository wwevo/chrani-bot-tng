from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_NORMAL
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = TELNET_TIMEOUT_NORMAL
    timeout_start = time()
    event_data[1]["action_identifier"] = action_name

    if not module.telnet.add_telnet_command_to_queue("getgamepref"):
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

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
        module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def validate_settings(regex, raw_gameprefs):
    gameprefs_dict = {}
    all_required_settings_are_available = False
    for m in re.finditer(regex, raw_gameprefs, re.MULTILINE):
        stripped_gameprefs = m.group("gamepref_value").rstrip()
        if all([
            len(stripped_gameprefs) >= 1,  # we have settings
            m.group("gamepref_name") == "GameName"  # the GameName setting is available!

        ]):
            all_required_settings_are_available = True

        gameprefs_dict[m.group("gamepref_name")] = stripped_gameprefs

    if all_required_settings_are_available:
        return gameprefs_dict
    else:
        return False


def callback_success(module, event_data, dispatchers_steamid, match=None):
    regex = (
        r"GamePref\.(?P<gamepref_name>.*)\s\=\s(?P<gamepref_value>.*)\s"
    )
    raw_gameprefs = match.group("raw_gameprefs")

    gameprefs_dict = validate_settings(regex, raw_gameprefs)
    if isinstance(gameprefs_dict, dict):
        current_game_name = gameprefs_dict.get("GameName", None)
        module.dom.data.upsert({
            module.get_module_identifier(): {
                current_game_name: {
                    "gameprefs": gameprefs_dict
                }
            }
        })

        module.dom.data.upsert({
            module.get_module_identifier(): {
                "active_dataset": current_game_name
            }
        })

        print("system:", "working with the \"{}\" dataset".format(current_game_name))
    else:
        print("system:", "stuff is missing. bot ain't working")


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
