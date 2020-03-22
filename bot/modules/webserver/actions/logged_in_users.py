from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(*args, **kwargs):
    module = args[0]
    event_data = args[1]
    event_data[1]["action_identifier"] = action_name

    try:
        connected_clients = list(module.connected_clients.keys())
    except AttributeError:
        callback_fail(*args, **kwargs)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "webserver_logged_in_users": connected_clients
        }
    })


def callback_success(*args, **kwargs):
    pass


def callback_fail(*args, **kwargs):
    pass


action_meta = {
    "description": "gets the current list of users currently logged into the webinterface",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
