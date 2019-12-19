from bot import loaded_modules_dict
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

    event_data = ['manage_authentication', {
        'dataset': module.dom.data.get("module_environment", {}).get("active_dataset", None),
        'player_steamid': steamid,
        'entered_password': entered_password,
        'action': 'set authentication'
    }]
    module.trigger_action_hook(origin_module, event_data=event_data)


trigger_meta = {
    "description": "validates a players password",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "password (Alloc)",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/password.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "password (BCM)",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\shandled\sby\smod\s\'(?P<used_mod>.*?)\':\s"
                r"Chat\s\(from\s\'(?P<player_steamid>.*?)\',\sentity\sid\s\'(?P<entity_id>.*?)\',\s"
                r"to\s\'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/password.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
