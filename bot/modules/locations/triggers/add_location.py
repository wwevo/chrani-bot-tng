from bot import loaded_modules_dict
from bot import telnet_prefixes
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

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    player_dict = module.dom.data.get("module_players", {}).get("elements", {}).get(active_dataset, {}).get(steamid, {})
    if len(player_dict) >= 1 and result:
        event_data = ['edit_location', {
            'location_coordinates': {
                "x": player_dict["pos"]["x"],
                "y": player_dict["pos"]["y"],
                "z": player_dict["pos"]["z"]
            },
            'location_name': location_name,
            'action': 'create_new',
            'last_changed': module.game_environment.get_last_recorded_gametime()
        }]
        module.trigger_action_hook(origin_module, event_data=event_data, dispatchers_steamid=steamid)


triggers = {
    "add location": r"\'(?P<player_name>.*)\'\:\s(?P<command>\/add location.*)"
}

trigger_meta = {
    "description": "catches location commands from the players chat and then adds them to the database",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "add location (Alloc)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["Allocs"]["chat"] +
                triggers["add location"]
            ),
            "callback": main_function
        },
        {
            "identifier": "add location (BCM)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["BCM"]["chat"] +
                triggers["add location"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
