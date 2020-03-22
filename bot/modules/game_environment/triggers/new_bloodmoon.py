from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    next_blood_moon = regex_result.group("next_BloodMoon")
    event_data = ['update_bloodmoon_date', {
        'blood_moon_date': next_blood_moon,
    }]
    module.trigger_action_hook(origin_module, event_data=event_data)


triggers = {
    "BloodMoon SetDay": r"BloodMoon\sSetDay:\sday\s(?P<next_BloodMoon>\d+)"
}

trigger_meta = {
    "description": "reacts to updated BloodMoon date in the telnet-stream",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                triggers["BloodMoon SetDay"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
