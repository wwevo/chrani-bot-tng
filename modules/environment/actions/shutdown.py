from modules import loaded_modules_dict
from os import path
from pathlib import Path

module_name = path.basename(path.dirname(Path(__file__).parent))
action_name = path.basename(Path(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid, *args, **kwargs):
    success = kwargs.get("success", False)
    if success == "True":
        callback_success(module, event_data, dispatchers_steamid, *args, **kwargs)
    else:
        callback_fail(module, event_data, dispatchers_steamid, *args, **kwargs)

    return


def callback_success(module, event_data, dispatchers_steamid, *args, **kwargs):
    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid, *args, **kwargs):
    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "shuts down the server",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
