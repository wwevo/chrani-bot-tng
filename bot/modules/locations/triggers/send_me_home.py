from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    player_steamid = regex_result.group("player_steamid")

    found_home = False
    location_dict = {}
    for home in origin_module.get_elements_by_type("is_home"):
        if home.get("owner") == player_steamid:
            location_dict = home
            found_home = True

    if found_home is True and len(location_dict) >= 1:
        event_data = ['management_tools', {
            'location_coordinates': {
                "x": location_dict["coordinates"]["x"],
                "y": location_dict["coordinates"]["y"],
                "z": location_dict["coordinates"]["z"]
            },
            'action': 'teleport'
        }]
        module.trigger_action_hook(origin_module, event_data=event_data, dispatchers_steamid=player_steamid)


trigger_meta = {
    "description": "sends the player to his home, if available",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "send me home",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/send\sme\shome)"
            ),
            "callback": main_function
        },
        {
            "identifier": "send me home",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\shandled\sby\smod\s\'(?P<used_mod>.*?)\':\s"
                r"Chat\s\(from\s\'(?P<player_steamid>.*?)\',\sentity\sid\s\'(?P<entity_id>.*?)\',\s"
                r"to\s\'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/send\sme\shome)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
