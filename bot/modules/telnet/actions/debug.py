from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    module.callback_success(callback_success, action_meta, dispatchers_id)
    return

def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return

def callback_skip(module, action_meta, dispatchers_id=None):
    return

def callback_fail(module, action_meta, dispatchers_id=None):
    return

action_meta = {
    "id": action_name,
    "description": "just demonstrating actions",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail,
    },
    "parameters": {
        "requires_telnet_connection": False,
        "disable_after_success": True,
        "enabled": True,
        "periodic": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
