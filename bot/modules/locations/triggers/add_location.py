from bot import loaded_modules_dict
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    steamid = regex_result.group("player_steamid")

    result = re.match(r"^.*add\slocation\s(?P<location_name>.*)", command)
    if result:
        location_name = result.group("location_name")

    current_map_identifier = module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName", None)

    player_dict = module.dom.data.get("module_players", {}).get("elements", {}).get(current_map_identifier, {}).get(steamid, {})
    if len(player_dict) >= 1 and result:
        event_data = ['manage_locations', {
                        'location_coordinates': {
                            "x": player_dict["pos"]["x"],
                            "y": player_dict["pos"]["y"],
                            "z": player_dict["pos"]["z"]
                        },
                        'location_name': location_name,
                        'action': 'create_new',
                        'last_changed': "n/A"
                    }]
        module.trigger_action_hook(origin_module, event_data, steamid)


trigger_meta = {
    "description": "catches location commands from the players chat and then adds them to the database",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "add location (Alloc)",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/add location.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "add location (BCM)",
            "regex": (

                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\shandled\sby\smod\s\'(?P<used_mod>.*?)\':\sChat\s\(from\s\'(?P<player_steamid>.*?)\',\sentity\sid\s\'(?P<entity_id>.*?)\',\s"
                r"to\s\'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/add location.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
