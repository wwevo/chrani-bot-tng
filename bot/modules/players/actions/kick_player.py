from bot import loaded_modules_dict
from os import path, pardir
from time import time, sleep
import json
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    event_data[1]["action_identifier"] = action_name
    action_is_confirmed = event_data[1].get("confirmed", "False")
    player_to_be_kicked = event_data[1].get("steamid", None)

    if action == "kick_player":
        if action_is_confirmed == "True":
            timeout = 5  # [seconds]
            timeout_start = time()

            reason = event_data[1].get("reason")

            command = "kick {} \"{}\"".format(player_to_be_kicked, reason)

            if not module.telnet.add_telnet_command_to_queue(command):
                module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
                return

            poll_is_finished = False
            """
            i was trying re.escape, string replacements... the only thing that seems to work is json.dumps for some
            reason
            """
            regex = (
                r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
                r"INF Executing\scommand\s\'" + re.escape(command) + r"\'\sby\sTelnet\sfrom\s(?P<called_by>.*)"
            ).replace('"', '\\"')

            while not poll_is_finished and (time() < timeout_start + timeout):
                sleep(0.25)
                match = False
                for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
                    poll_is_finished = True

                if match:
                    module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
                    return

        else:
            module.dom.data.upsert({
                "module_players": {
                    "visibility": {
                        dispatchers_steamid: {
                            "current_view": "kick-modal",
                            "current_view_steamid": player_to_be_kicked
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)
            return

    elif action == "cancel_kick_player":
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    module.dom.data.upsert({
        "module_players": {
            "visibility": {
                dispatchers_steamid: {
                    "current_view": "frontend",
                    "current_view_steamid": None
                }
            }
        }
    }, dispatchers_steamid=dispatchers_steamid)


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "kicks a player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
