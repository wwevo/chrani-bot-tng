from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    """
    Toggles between different widget views.

    Event data format:
    {
        'view': str  # "frontend" or "scenarios"
    }
    """
    event_data[1]["action_identifier"] = action_name

    view = event_data[1].get("view", "frontend")

    # Update the current view in DOM
    module.set_current_view(dispatchers_steamid, {
        "current_view": view
    })

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "Toggles between widget views",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
