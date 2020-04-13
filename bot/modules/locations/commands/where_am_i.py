from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def find_by_key(data, target):
    for key, value in data.items():
        if isinstance(value, dict):
            yield from find_by_key(value, target)
        elif key == target:
            yield value


def main_function(origin_module, module, regex_result):
    player_steamid = regex_result.group("player_steamid")
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    player_dict = (
        module.dom.data.get("module_players", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(player_steamid, {})
    )

    all_locations_dict = (
        module.dom.data.get("module_locations", {})
        .get("elements", {})
        .get(active_dataset, {})
    )

    occupied_locations = []
    for locations_by_owner in all_locations_dict:
        for location_identifier, location_dict in all_locations_dict[locations_by_owner].items():
            if origin_module.position_is_inside_boundary(player_dict, location_dict):
                occupied_locations.append(location_dict)

    if len(occupied_locations) > 0:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FFFFFF]You are inside the following locations:[-]'
        }]
        module.trigger_action_hook(origin_module.players, event_data=event_data)

        for location_dict in occupied_locations:
            location_owner_dict = (
                module.dom.data.get("module_players", {})
                .get("elements", {})
                .get(active_dataset, {})
                .get(location_dict.get("owner"), {})
            )

            event_data = ['say_to_player', {
                'steamid': player_steamid,
                'message': '[FFFFFF]{name} [66FF66]({owner})[-]'.format(
                    name=location_dict.get("name", "n/a"),
                    owner=location_owner_dict.get("name", "n/a")
                )
            }]
            module.trigger_action_hook(origin_module.players, event_data=event_data)
    else:
        event_data = ['say_to_player', {
            'steamid': player_steamid,
            'message': '[FFFFFF]You do not seem to be in any designated location[-]'
        }]
        module.trigger_action_hook(origin_module.players, event_data=event_data)


triggers = {
    "where am i": r"\'(?P<player_name>.*)\'\:\s(?P<command>\/where am i)"
}

trigger_meta = {
    "description": "prints out a list of locations a player currently occupies",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "where am i (Allocs)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["Allocs"]["chat"] +
                triggers["where am i"]
            ),
            "callback": main_function
        },
        {
            "identifier": "where am i (BCM)",
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["BCM"]["chat"] +
                triggers["where am i"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
