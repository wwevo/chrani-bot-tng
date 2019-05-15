from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    player_steamid = event_data[1].get("steamid", None)
    if action is not None and player_steamid is not None:
        if action == "show_options":
            module.dom.data.upsert({
                "module_players": {
                    "visibility": {
                        dispatchers_steamid: {
                            "current_view": "options",
                            "current_view_steamid": None
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)
        if action == "show_frontend":
            module.dom.data.upsert({
                "module_players": {
                    "visibility": {
                        dispatchers_steamid: {
                            "current_view": "frontend",
                            "current_view_steamid": None
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)
        if action == "show_info_view":
            module.dom.data.upsert({
                "module_players": {
                    "visibility": {
                        dispatchers_steamid: {
                            "current_view": "info_view",
                            "current_view_steamid": player_steamid
                        }
                    }
                }
            }, dispatchers_steamid=dispatchers_steamid)

        callback_success(module, event_data, dispatchers_steamid)
        return

    callback_fail(module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid):
    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid):
    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "manages player entries",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
