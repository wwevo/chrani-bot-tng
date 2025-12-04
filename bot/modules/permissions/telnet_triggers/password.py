from bot import loaded_modules_dict
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, trigger_meta, dispatchers_id=None):
    regex_result = trigger_meta["regex_result"]
    source_module = trigger_meta["source_module"]

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
    module.trigger_action_hook(source_module, event_data=event_data)


triggers = {
    "password": r"\'(?P<player_name>.*)\'\:\s(?P<command>\/password.*)"
}

trigger_meta = {
    "description": "validates a players password",
    "main_function": main_function,
    "triggers": []
}

loaded_modules_dict["module_" + module_name].register_telnet_trigger(trigger_name, trigger_meta)
