from bot import loaded_modules_dict
from bot import telnet_prefixes
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


triggers = {
    "when is hordenight": r"\'(?P<player_name>.*)\'\:\s(?P<command>\/when\sis\shordenight)"
}

trigger_meta = {
    "description": "tells the player when the next bloodmoon will hit",
    "main_function": main_function,
    "triggers": [
        {
            "identifier": "when is hordenight (Allocs)",
            "regex": (
                    telnet_prefixes["telnet_log"]["timestamp"] +
                    telnet_prefixes["Allocs"]["chat"] +
                    triggers["when is hordenight"]
            ),
            "callback": main_function
        },
        {
            "identifier": "when is hordenight (BCM)",
            "regex": (
                    telnet_prefixes["telnet_log"]["timestamp"] +
                    telnet_prefixes["BCM"]["chat"] +
                    triggers["when is hordenight"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
