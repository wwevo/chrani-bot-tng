from bot import loaded_modules_dict
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    player_steamid = regex_result.group("player_steamid")

    result = re.match(r"^.*send\sme\sto\slocation\s(?P<location_identifier>.*)", command)
    if result:
        location_identifier = result.group("location_identifier")
    else:
        return

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    location_dict = (
        module.dom.data.get("module_locations", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(player_steamid, {})
        .get(location_identifier, {})
    )

    player_dict = (
        module.dom.data.get("module_players", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(player_steamid, {})
    )

    if len(player_dict) >= 1 and len(location_dict) >= 1:
        event_data = ['teleport_to_coordinates', {
            'location_coordinates': {
                "x": location_dict.get("teleport_entry", {}).get("x", location_dict["coordinates"]["x"]),
                "y": location_dict.get("teleport_entry", {}).get("y", location_dict["coordinates"]["y"]),
                "z": location_dict.get("teleport_entry", {}).get("z", location_dict["coordinates"]["z"])
            }
        }]
        module.trigger_action_hook(origin_module, event_data=event_data, dispatchers_steamid=player_steamid)


trigger_meta = {
    "description": (
        "sends player to the location of their choosing, will use the teleport_entry coordinates if available"
    ),
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "add location (Alloc)",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/send\sme\sto\slocation.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "add location (BCM)",
            "regex": (

                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\shandled\sby\smod\s\'(?P<used_mod>.*?)\':\sChat\s\(from\s\'(?P<player_steamid>.*?)\',\sentity\sid\s\'(?P<entity_id>.*?)\',\s"
                r"to\s\'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/send\sme\sto\slocation.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)