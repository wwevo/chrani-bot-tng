from bot import loaded_modules_dict
from os import path, pardir


module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]

def main_function(module, event_data, dispatchers_steamid=None):
    module.save_dom_to_persistent_dict()


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    return

def callback_skip(module, action_meta, dispatchers_id=None):
    return

def callback_fail(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "id": action_name,
    "description": "writes storage.json to disc",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail
    },
    "parameters": {
        "enabled": True,
        "periodic": True,
        "requires_telnet_connection": False,
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
