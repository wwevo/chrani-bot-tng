from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    if action is not None:
        if action == "disable_telnet_data_transfer":
            module.data_transfer_enabled = False
            module.dom.data.upsert({
                "module_telnet": {
                    "data_transfer_enabled": False
                }
            }, dispatchers_steamid=dispatchers_steamid)
        if action == "enable_telnet_data_transfer":
            module.data_transfer_enabled = True
            module.dom.data.upsert({
                "module_telnet": {
                    "data_transfer_enabled": True
                }
            }, dispatchers_steamid=dispatchers_steamid)

        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "enables or disables active telnet usage. logs will be read!",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
