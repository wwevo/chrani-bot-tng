from bot import loaded_modules_dict
from os import path, pardir
from time import time

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    module.dom.data.upsert({
        "module_game_environment": {
            active_dataset: {
                "cancel_shutdown": True,
                "shutdown_in_seconds": None,
                "force_shutdown": False
            }
        }
    })

    event_data = ['say_to_all', {
        'message': (
            'a [FF6666]scheduled shutdown[-] has been cancelled.'
        )
    }]
    module.trigger_action_hook(module, event_data=event_data)

    """ stop the timer """


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "Set the (active) shutdown procedure to be cancelled",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
