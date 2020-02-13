from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    position_dict = {
        "pos": {
            "x":  regex_result.group("pos_x"),
            "y": regex_result.group("pos_y"),
            "z": regex_result.group("pos_z")
        }
    }
    zombie_id = regex_result.group("entity_id")
    zombie_name = regex_result.group("zombie_name")
    screamer_safe_locations = origin_module.default_options.get("screamer_safe_locations", [])

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if zombie_name == "zombieScreamer":
        for location in screamer_safe_locations:
            location_owner = location.get("owner", None)
            location_identifier = location.get("identifier", None)

            location_dict = (
                module.dom.data
                .get("module_locations", {})
                .get("elements", {})
                .get(active_dataset, {})
                .get(location_owner, {})
                .get(location_identifier)
            )

            if origin_module.locations.position_is_inside_boundary(position_dict, location_dict):
                event_data = ['manage_entities', {
                    'dataset': active_dataset,
                    'entity_id': zombie_id,
                    'entity_name': zombie_name,
                    'action': 'kill'
                }]
                module.trigger_action_hook(origin_module.game_environment, event_data=event_data)  # no steamid cause it's a system_call

                event_data = ['say_to_all', {
                    'message': (
                        '[FF6666]Screamer ([FFFFFF]{entity_id}[FF6666]) spawned[-] '
                        '[FFFFFF]inside [CCCCFF]{location_name}[FFFFFF].[-]'.format(
                            entity_id=zombie_id,
                            location_name=location_dict.get("name")
                        )
                    )
                }]
                module.trigger_action_hook(origin_module.game_environment, event_data=event_data)
                # we only need to match one location. even though a screamer can be in multiple locations at once,
                # we stil only have to kill it once :)
                break
        else:
            event_data = ['say_to_all', {
                'message': (
                    '[FF6666]Screamer ([FFFFFF]{entity_id}[FF6666]) spawned[-] '
                    '[CCCCFF]somewhere[FFFFFF]...[-]'.format(
                        entity_id=zombie_id
                    )
                )
            }]
            module.trigger_action_hook(origin_module.game_environment, event_data=event_data)


trigger_meta = {
    "description": "reacts to spawning zombies (screamers, mostly)",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>.+?)\s"
                r"INF (?P<command>.+?)\s"
                r"\["
                r"type=(.*),\s"
                r"name=(?P<zombie_name>.+?),\s"
                r"id=(?P<entity_id>.*)\]\sat\s\((?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)\)\s"
                r"Day=(\d.*)\s"
                r"TotalInWave=(\d.*)\s"
                r"CurrentWave=(\d.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
