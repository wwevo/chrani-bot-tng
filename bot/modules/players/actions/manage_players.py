from bot import loaded_modules_dict
from os import path, pardir
from builtins import int

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    player_steamid = event_data[1].get("steamid", None)

    if all([
        player_steamid is not None
    ]):
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    action = event_data[1].get("action", None)
    player_steamid = event_data[1].get("steamid", None)


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages player entries",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
