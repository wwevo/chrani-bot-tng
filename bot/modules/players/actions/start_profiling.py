from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    event_data[1]["action_identifier"] = action_name

    # Start tracking manually
    from bot.tracking import tracker

    if not tracker._enabled:
        event_data[1]["fail_reason"] = ["PROFILING_ENABLED is not set"]
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    if tracker._test_start is not None:
        event_data[1]["fail_reason"] = ["Tracking already active"]
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    # Manually activate tracking for 'lp' command
    tracker.start_tracking("lp")

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    # Refresh the profiling view to show updated status
    module.set_current_view(dispatchers_steamid, {
        "current_view": "profiling",
        "current_view_steamid": None
    })


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "starts performance profiling test for LP commands",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
