from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    steamid = regex_result.group("player_steamid")

    result = re.match(r"^.*password\s(?P<password>.*)", command)
    if result:
        entered_password = result.group("password")
    else:
        return

    event_data = ['set_authentication', {
        'dataset': module.dom.data.get("module_game_environment", {}).get("active_dataset", None),
        'player_steamid': steamid,
        'entered_password': entered_password
    }]
    module.trigger_action_hook(origin_module, event_data=event_data)


trigger_meta = {
    "description": "validates a players password",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "password (Alloc)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["Allocs"]["chat"] +
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/password.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "password (BCM)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["BCM"]["chat"] +
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/password.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
