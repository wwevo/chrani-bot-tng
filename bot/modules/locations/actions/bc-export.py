from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    location_identifier = event_data[1].get("location_identifier")
    location_dict = (
        module.dom.data.get("module_locations", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(dispatchers_steamid, {})
        .get(location_identifier, None)
    )

    coordinates = module.get_location_volume(location_dict)
    if coordinates is not None:
        command = (
            "bc-export {location_to_be_exported} {pos_x} {pos_y} {pos_z} {pos_x2} {pos_y2} {pos_z2}"
        ).format(
            location_to_be_exported=location_dict.get("identifier"),
            **coordinates
        )

        print(command)
        module.telnet.add_telnet_command_to_queue(command)
        module.callback_success(callback_success, module, event_data, dispatchers_steamid)
        return

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "Will export everything inside the locations Volume.",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
