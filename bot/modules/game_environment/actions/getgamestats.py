from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_NORMAL, TELNET_PREFIXES
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    # we can't save the gamestats without knowing the game-name, as each game can have different stats.
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    timeout_start = time()

    if module.telnet.add_telnet_command_to_queue("getgamestat"):
        regex = action_meta.get("regex")[0]

        poll_is_finished = False

        timeout_end = timeout_start + TELNET_TIMEOUT_NORMAL
        while not poll_is_finished and (time() < timeout_end):
            sleep(0.25)  # give the telnet a little time to respond so we have a chance to get the data at first try
            for match in re.finditer(regex, module.telnet.telnet_buffer, re.MULTILINE):
                poll_is_finished = True
                module.callback_success(callback_success, action_meta, dispatchers_id, match)

        if not poll_is_finished :
            action_meta["fail_reason"] = []
            action_meta["fail_reason"].append("timed out waiting for response")
    else:
        action_meta["fail_reason"] = []
        action_meta["fail_reason"].append("action already queued up")

    module.callback_fail(callback_fail, action_meta, dispatchers_id)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    regex = action_meta.get("regex")[1]

    raw_gamestats = match.group("raw_gamestats")
    gamestats_dict = {}

    for m in re.finditer(regex, raw_gamestats, re.MULTILINE):
        gamestats_dict[m.group("gamestat_name")] = m.group("gamestat_value").rstrip()

    active_dataset = (
        module.dom.data
        .get(module.get_module_identifier())
        .get("active_dataset", None)
    )

    module.dom.data.upsert({
        module.get_module_identifier(): {
            active_dataset: {
                "gamestats": gamestats_dict
            }
        }
    })


def callback_skip(module, action_meta, dispatchers_id=None):
    print("skipped {}".format(action_meta.get("id")))


def callback_fail(module, action_meta, dispatchers_id=None):
    if action_meta.get("fail_reason"):
        print(action_meta.get("fail_reason"))


action_meta = {
    "id": action_name,
    "description": "gets a list of all current game-stats",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_fail": callback_fail
    },
    "parameters": {
        "enabled": True,
        "periodic": True,
        "disable_after_success": True,
        "requires_telnet_connection": True
    },
    "regex": [
        (
            TELNET_PREFIXES["telnet_log"]["timestamp"] +
            r"Executing\scommand\s\'getgamestat\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
            r"(?P<raw_gamestats>(?:GameStat\..*?\r?\n)+)"
        ),
        (
            r"GameStat\.(?P<gamestat_name>.*)\s\=\s(?P<gamestat_value>.*)\s"
        )
    ]
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
