from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir
from time import time, sleep
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
            """
            i was trying re.escape, string replacements... the only thing that seems to work is all of them together
            Had some big trouble filtering out stuff like ^ and " and whatnot
            """
            regex = (
                telnet_prefixes["telnet_log"]["timestamp"] +
                r"Executing\scommand\s\'" + re.escape(command) + r"\'\s"
                r"by\sTelnet\s"
                r"from\s(?P<called_by>.*)"
            ).replace('"', '\\"')

            print(command)
            print(regex)

            if not module.telnet.add_telnet_command_to_queue(command):
                module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
                return

            poll_is_finished = False
            while not poll_is_finished and (time() < timeout_start + timeout):
                sleep(0.25)
                match = False
                for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
                    poll_is_finished = True

                if match:
                    module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
                    return

        else:
            module.set_current_view(dispatchers_steamid, {
                "current_view": "kick-modal",
                "current_view_steamid": player_to_be_kicked
            })
            return

    elif action == "cancel_kick_player":
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    module.set_current_view(dispatchers_steamid, {
        "current_view": "frontend",
    })


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
