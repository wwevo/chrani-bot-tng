from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    next_bloodmoon_date = event_data[1].get("blood_moon_date", None)
    if next_bloodmoon_date is not None:
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    next_bloodmoon_date = event_data[1].get("blood_moon_date", None)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            active_dataset: {
                "gamestats": {
                    "BloodMoonDay": next_bloodmoon_date
                }
            }
        }
    })


def callback_fail(module, event_data, dispatchers_steamid):
    pass


def skip_it(module, event_data, dispatchers_steamid=None):
    pass


action_meta = {
    "description": "updates bloodmoon date",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "skip_it": skip_it,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
