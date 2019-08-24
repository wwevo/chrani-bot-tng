from bot import loaded_modules_dict
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    location_identifier = "PlaceofDeath"
    current_map_identifier = (
        module.dom.data.get("module_environment", {})
        .get("gameprefs", {})
        .get("GameName", None)
    )

    steamid = regex_result.group("player_steamid")
    player_dict = module.dom.data.get("module_players", {}).get("players", {}).get(steamid, {})
    location_dict = (
        module.dom.data.get("module_locations", {})
            .get("elements", {})
            .get(current_map_identifier, {})
            .get(steamid, {})
            .get(location_identifier, {})
    )

    if len(player_dict) >= 1 and len(location_dict) >= 1:
        event_data = ['management_tools', {
                        'location_coordinates': {
                            "x": location_dict["coordinates"]["x"],
                            "y": location_dict["coordinates"]["y"],
                            "z": location_dict["coordinates"]["z"]
                        },
                        'action': 'teleport'
                    }]
        module.trigger_action_hook(origin_module, event_data, steamid)


trigger_meta = {
    "description": "sends the player to his final resting place, if available",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "take me to my grave",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/take me to my grave)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
