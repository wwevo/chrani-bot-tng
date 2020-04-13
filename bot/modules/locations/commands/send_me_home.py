from bot import loaded_modules_dict
from bot import telnet_prefixes
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
        event_data = ['teleport_to_coordinates', {
            'location_coordinates': {
                "x": location_dict.get("teleport_entry", {}).get("x", location_dict["coordinates"]["x"]),
                "y": location_dict.get("teleport_entry", {}).get("y", location_dict["coordinates"]["y"]),
                "z": location_dict.get("teleport_entry", {}).get("z", location_dict["coordinates"]["z"])
            }
        }]
        module.trigger_action_hook(origin_module, event_data=event_data, dispatchers_steamid=player_steamid)


triggers = {
    "send me home": r"\'(?P<player_name>.*)\'\:\s(?P<command>\/send\sme\shome)"
}

trigger_meta = {
    "description": "sends the player to his home, if available",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "send me home",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["Allocs"]["chat"] +
                triggers["send me home"]
            ),
            "callback": main_function
        },
        {
            "identifier": "send me home",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["BCM"]["chat"] +
                triggers["send me home"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
