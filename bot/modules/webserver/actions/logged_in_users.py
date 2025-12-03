from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    if module.connected_clients.keys():
        module.callback_success(callback_success, action_meta, dispatchers_id)
    else:
        action_meta["fail_reason"] = ["[{}]: {}".format(action_name, "no clients found")]
        module.callback_fail(callback_fail, action_meta, dispatchers_id)


def callback_success(module, action_meta, dispatchers_id=None):
    connected_clients = list(module.connected_clients.keys())

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "webserver_logged_in_users": connected_clients
        }
    })

def callback_fail(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "id": action_name,
    "description": "gets the current list of users currently logged into the webinterface",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_fail": callback_fail
    },
    "parameters": {
        "periodic": True,
        "requires_telnet_connection": True,
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
