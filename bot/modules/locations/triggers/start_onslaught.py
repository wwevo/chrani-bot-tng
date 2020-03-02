from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    steamid = regex_result.group("player_steamid")
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    player_dict = (
        module.dom.data.get("module_players", {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(steamid, {})
    )

    if len(player_dict) < 1:
        return False

    result = re.match(r"^.*st.*\sonslaught\s(?P<onslaught_options>.*)", command)
    if result:
        onslaught_options = result.group("onslaught_options")
    else:
        """ no options provided
        might later chose the location one is standing in and owns, or let some other stuff happen 
        """
        onslaught_options = None

    if command.startswith("/start onslaught"):
        """ check if the player is inside a location which allows onslaught to be enabled """
        # let's iterate through all suitable locations
        for onslaught_location in origin_module.get_elements_by_type("is_onslaught"):
            # only proceed with the player is inside a dedicated location
            if any([
                onslaught_options in ["everywhere", onslaught_location["identifier"]],
                origin_module.position_is_inside_boundary(player_dict, onslaught_location)
            ]):
                # fire onslaught in all selected locations
                event_data = ['onslaught', {
                    'onslaught_options': onslaught_options,
                    'location_owner': onslaught_location['owner'],
                    'location_identifier': onslaught_location['identifier'],
                    'action': 'start onslaught'
                }]
                module.trigger_action_hook(origin_module, event_data=event_data, dispatchers_steamid=steamid)

    elif command.startswith("/stop onslaught"):
        for onslaught_location in origin_module.get_elements_by_type("is_onslaught"):
            # only proceed with the player is inside a dedicated location
            if any([
                onslaught_options in ["everywhere", onslaught_location["identifier"]],
                origin_module.position_is_inside_boundary(player_dict, onslaught_location)
            ]):
                # fire onslaught in all selected locations
                event_data = ['onslaught', {
                    'location_owner': onslaught_location['owner'],
                    'location_identifier': onslaught_location['identifier'],
                    'action': 'stop onslaught'
                }]
                module.trigger_action_hook(origin_module, event_data=event_data, dispatchers_steamid=steamid)


trigger_meta = {
    "description": "will start the onslaught event in a specified location",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "start onslaught (Alloc)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["Allocs"]["chat"] +
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/start\sonslaught.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "stop onslaught (Alloc)",
            "regex": (
                    telnet_prefixes["telnet_log"]["timestamp"] +
                    telnet_prefixes["Allocs"]["chat"] +
                    r"\'(?P<player_name>.*)\'\:\s(?P<command>\/stop\sonslaught.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "start onslaught (BCM)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["BCM"]["chat"] +
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/start\sonslaught.*)"
            ),
            "callback": main_function
        },
        {
            "identifier": "stop onslaught (BCM)",
            "regex": (
                    telnet_prefixes["telnet_log"]["timestamp"] +
                    telnet_prefixes["BCM"]["chat"] +
                    r"\'(?P<player_name>.*)\'\:\s(?P<command>\/stop\sonslaught.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
