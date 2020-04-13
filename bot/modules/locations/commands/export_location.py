from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    player_steamid = regex_result.group("player_steamid")

    location_dict = None
    result = re.match(r"^.*export\slocation\s(?P<location_identifier>.*)(?:\s)?(?P<spawn_in_place>.*)?", command)
    if result:
        active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
        location_identifier = result.group("location_identifier")
        location_dict = (
            module.dom.data.get("module_locations", {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(player_steamid, {})
            .get(location_identifier, None)
        )
        location_name = location_dict.get("name")
    else:
        location_name = "None Provided"
        location_identifier = "None"

    if location_dict is not None:
        event_data = ['bc-export', {
            "location_identifier": location_identifier
        }]
        module.trigger_action_hook(origin_module.locations, event_data=event_data, dispatchers_steamid=player_steamid)

    else:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FFFFFF]Could not find [66FF66]{location_name} ({location_identifier})[-]'.format(
                location_name=location_name,
                location_identifier=location_identifier
            )
        }]
        module.trigger_action_hook(origin_module.players, event_data=event_data)


triggers = {
    "export location": r"\'(?P<player_name>.*)\'\:\s(?P<command>\/export location.*)"
}

trigger_meta = {
    "description": "will issue the BCM mods bc-export command on the specified location",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "export location",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["Allocs"]["chat"] +
                triggers["export location"]
            ),
            "callback": main_function
        },
        {
            "identifier": "export location",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["BCM"]["chat"] +
                triggers["export location"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
