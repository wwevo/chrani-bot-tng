from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_NORMAL, TELNET_PREFIXES
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    timeout_start = time()
    if module.telnet.add_telnet_command_to_queue("getgamepref"):
        poll_is_finished = False
        regex = action_meta.get("regex")[0]

        timeout_end = timeout_start + TELNET_TIMEOUT_NORMAL
        while not poll_is_finished and (time() < timeout_end):
            sleep(0.25)

            match = re.search(regex, module.telnet.telnet_buffer, re.MULTILINE)
            if match:
                poll_is_finished = True
                module.callback_success(callback_success, action_meta, dispatchers_id, match)

        if not poll_is_finished:
            action_meta["fail_reason"] = []
            action_meta["fail_reason"].append("timed out waiting for response")
    else:
        action_meta["fail_reason"] = []
        action_meta["fail_reason"].append("action already queued up")

    module.callback_fail(callback_fail, action_meta, dispatchers_id)


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


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    regex = action_meta.get("regex")[1]
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
    else:
        print("gameprefs_validation_failed")


def callback_skip(module, action_meta, dispatchers_id=None):
    print("skipped {}".format(action_meta.get("id")))

def callback_fail(module, action_meta, dispatchers_id=None):
    if action_meta.get("fail_reason"):
        print(action_meta.get("fail_reason"))


action_meta = {
    "id": action_name,
    "description": "gets a list of all current game-preferences",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_fail": callback_fail
    },
    "parameters": {
        "enabled": True,
        "periodic": True,
        "disable_after_success": True,
        "requires_telnet_connection": True,
    },
    "regex": [
        (
            TELNET_PREFIXES["telnet_log"]["timestamp"] +
            r"Executing\scommand\s\'getgamepref\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
            r"(?P<raw_gameprefs>(?:GamePref\..*?\r?\n)+)"
        ),
        (
            r"GamePref\.(?P<gamepref_name>.*)\s\=\s(?P<gamepref_value>.*)\s"
        )
    ]
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
