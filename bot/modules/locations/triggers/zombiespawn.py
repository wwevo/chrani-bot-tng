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

    zombie_name = regex_result.group("zombie_name")
    print(zombie_name)

    current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)
    if zombie_name == "zombieScreamer":
        village_dict = (
            module.dom.data
            .get("module_locations", {})
            .get("elements", {})
            .get(current_map_identifier, {})
            .get("76561198040658370", {})
            .get("Chraniville", {})
        )
        if origin_module.locations.position_is_inside_boundary(position_dict, village_dict):
            event_data = ['say_to_all', {
                'message': '[FF6666]Screamer spawned[-] [FFFFFF]inside {}[-]'.format(village_dict.get("name"))
            }]
        else:
            event_data = ['say_to_all', {
                'message': '[FF6666]Screamer spawned[-] [FFFFFF]somewhere...[-]'
            }]

        module.trigger_action_hook(origin_module.players, event_data)


trigger_meta = {
    "description": "reacts to spawning zombies",
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
