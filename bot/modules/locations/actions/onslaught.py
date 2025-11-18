from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    event_data[1]["action_identifier"] = action_name
    location_identifier = event_data[1].get("location_identifier", None)

    if action == "start onslaught":
        event_data = ['say_to_player', {
            'steamid': dispatchers_steamid,
            'message': '[66FF66]Onslaught[-][FFFFFF] Started for location [66FF66]{}[-]'.format(location_identifier)
        }]
        module.trigger_action_hook(module.players, event_data=event_data)
    elif action == "stop onslaught":
        event_data = ['say_to_player', {
            'steamid': dispatchers_steamid,
            'message': '[66FF66]Onslaught[-][FFFFFF] in location [66FF66]{}[-] Ended[-]'.format(location_identifier)
        }]
        module.trigger_action_hook(module.players, event_data=event_data)

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages the onslaught event on dedicated locations",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
