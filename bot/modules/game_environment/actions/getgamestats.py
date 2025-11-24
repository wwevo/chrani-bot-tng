from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_NORMAL
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    # we can't save the gamestats without knowing the game-name, as each game can have different stats.
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)

    timeout_start = time()
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    if module.telnet.add_telnet_command_to_queue("getgamestat"):
        regex = (
            r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
            r"INF Executing\scommand\s\'getgamestat\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
            r"(?P<raw_gamestats>(?:GameStat\..*?\r?\n)+)"
        )
        poll_is_finished = False

        while not poll_is_finished and (time() < timeout_start + TELNET_TIMEOUT_NORMAL):
            sleep(0.25)  # give the telnet a little time to respond so we have a chance to get the data at first try
            for match in re.finditer(regex, module.telnet.telnet_buffer, re.MULTILINE):
                poll_is_finished = True
                module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)

        event_data[1]["fail_reason"].append("timed out waiting for response")
    else:
        event_data[1]["fail_reason"].append("action already queued up")

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    regex = (
        r"GameStat\.(?P<gamestat_name>.*)\s\=\s(?P<gamestat_value>.*)\s"
    )
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


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "gets a list of all current game-stats",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
