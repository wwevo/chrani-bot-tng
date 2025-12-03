from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        if not (action_meta.get("fail_reason")):
            action_meta["fail_reason"] = []

        action_meta["fail_reason"].append("an active dataset needs to be present")
        module.callback_fail(callback_fail, action_meta, dispatchers_id)
        return

    if action_meta.get("parameters").get("requires_connected_clients") and not module.webserver.connected_clients:
        if not (action_meta.get("skip_reason")):
            action_meta["skip_reason"] = []

        action_meta["skip_reason"].append("no one around to see it")
        module.callback_skip(callback_skip, action_meta, dispatchers_id)
        return

    action_data = action_meta.get("action_data")
    if not action_data.get("widget_view"):
        module.callback_fail(callback_fail, action_meta, dispatchers_id)
        return

    widget_id = action_meta.get("action_data").get("id")
    target_module = loaded_modules_dict[action_data.get("widget_module")]
    target_module.set_current_view(dispatchers_id, {
        "{}_view".format(widget_id): action_data.get("widget_view")
    })
    module.callback_success(callback_success, action_meta, dispatchers_id)


def callback_success(module, action_meta, dispatchers_id=None, match=None):
    pass


def callback_skip(module, action_data, dispatchers_id=None):
    print("skipped {}".format(action_data.get("id")))


def callback_fail(module, action_data, dispatchers_id=None):
    print("fail {}".format(action_data.get("id")))
    if action_data.get("fail_reason"):
        print(action_data.get("fail_reason"))


action_meta = {
    "id": action_name,
    "description": "Manages a widgets main view",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_skip": callback_skip,
        "callback_fail": callback_fail
    },
    "parameters": {
        "requires_connected_clients": True,
        "requires_telnet_connection": False,
        "enabled": True
    }
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
