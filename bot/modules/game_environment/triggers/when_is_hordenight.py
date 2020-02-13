from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    next_bloodmoon_date = (
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("gamestats", {})
        .get("BloodMoonDay", None)
    )
    event_data = ['say_to_all', {
        'message': 'Next [FFCCCC]hordenight[FFFFFF] will be on day {day}[-]'.format(
            day=next_bloodmoon_date
        )
    }]
    module.trigger_action_hook(module, event_data=event_data)


trigger_meta = {
    "description": "tells the player when the next bloodmoon will hit",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "when is hordenight",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\s\(from \'(?P<player_steamid>.*)\',\sentity\sid\s\'(?P<entity_id>.*)\',\s"
                r"to \'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/when\sis\shordenight)"
            ),
            "callback": main_function
        },
        {
            "identifier": "when is hordenight",
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Chat\shandled\sby\smod\s\'(?P<used_mod>.*?)\':\s"
                r"Chat\s\(from\s\'(?P<player_steamid>.*?)\',\sentity\sid\s\'(?P<entity_id>.*?)\',\s"
                r"to\s\'(?P<target_room>.*)\'\)\:\s"
                r"\'(?P<player_name>.*)\'\:\s(?P<command>\/when\sis\shordenight)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
