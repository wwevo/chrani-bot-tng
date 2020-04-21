from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    shutdown_in_seconds = int(event_data[1]["shutdown_in_seconds"])
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    module.dom.data.upsert({
        "module_game_environment": {
            active_dataset: {
                "cancel_shutdown": False,
                "shutdown_in_seconds": shutdown_in_seconds,
                "force_shutdown": False
            }
        }
    })

    event_data = ['say_to_all', {
        'message': (
            'a [FF6666]scheduled shutdown[-] is about to take place!'
            'shutdown in {seconds} seconds'.format(
                seconds=shutdown_in_seconds
            )
        )
    }]
    module.trigger_action_hook(module, event_data=event_data)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "Sets the schedule for a shutdown",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
