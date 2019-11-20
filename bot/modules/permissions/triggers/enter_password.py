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

    if origin_module.default_options.get("player_password", None) == entered_password:
        is_authenticated = True
        event_data = ['say_to_player', {
            'steamid': steamid,
            'message': '[66FF66]Thank you for playing along[-][FFFFFF], you may now leave the Crater[-]'
        }]
        module.trigger_action_hook(origin_module.players, event_data, steamid)

    else:
        is_authenticated = False

    current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)
    module.dom.data.upsert({
        "module_players": {
            "elements": {
                current_map_identifier: {
                    steamid: {
                        "is_authenticated": is_authenticated
                    }
                }
            }
        }
    })


trigger_meta = {
    "description": "sends player to the location of their choosing",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "add location (Alloc)",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/password.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "add location (BCM)",
            "regex": (

                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\shandled\sby\smod\s\'(?P<used_mod>.*?)\':\sChat\s\(from\s\'(?P<player_steamid>.*?)\',\sentity\sid\s\'(?P<entity_id>.*?)\',\s"
                r"to\s\'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/password.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
