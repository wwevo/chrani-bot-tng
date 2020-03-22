from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def fix_coordinates_for_bc_import(location_dict, coordinates, player_dict=None):
    shape = location_dict.get("shape", None)
    dimensions = location_dict.get("dimensions", None)
    location_coordinates = location_dict.get("coordinates", None)

    if shape == "box":
        if player_dict is None:
            if int(float(location_coordinates["x"])) < 0:  # W Half
                coordinates["pos_x"] = int(float(coordinates["pos_x"]) - float(dimensions["width"]) + 1)
            if int(float(location_coordinates["x"])) >= 0:  # E Half
                coordinates["pos_x"] = int(float(coordinates["pos_x"]) - float(dimensions["width"]))
        else:
            if int(float(player_dict.get("pos", {}).get("x"))) < 0:  # W Half
                coordinates["pos_x"] = int(float(player_dict.get("pos", {}).get("x")) - float(dimensions["width"]) - 1)
            if int(float(player_dict.get("pos", {}).get("x"))) >= 0:  # E Half
                coordinates["pos_x"] = int(float(player_dict.get("pos", {}).get("x")) - float(dimensions["width"]))

            coordinates["pos_y"] = int(float(player_dict.get("pos", {}).get("y")))

            if int(float(player_dict.get("pos", {}).get("z"))) < 0:  # S Half
                coordinates["pos_z"] = int(float(player_dict.get("pos", {}).get("z")) - 1)
            if int(float(player_dict.get("pos", {}).get("z"))) >= 0:  # N Half
                coordinates["pos_z"] = int(float(player_dict.get("pos", {}).get("z")))


def main_function(module, event_data, dispatchers_steamid):
    event_data[1]["action_identifier"] = action_name

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    location_identifier = event_data[1].get("location_identifier")
    spawn_in_place = event_data[1].get("spawn_in_place")
    location_dict = (
        module.dom.data.get("module_locations", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(dispatchers_steamid, {})
        .get(location_identifier, None)
    )

    coordinates = module.get_location_volume(location_dict)

    if coordinates is not None:
        if spawn_in_place:
            player_dict = (
                module.dom.data.get("module_players", {})
                    .get("elements", {})
                    .get(active_dataset, {})
                    .get(dispatchers_steamid, {})
            )
            fix_coordinates_for_bc_import(location_dict, coordinates, player_dict)
        else:
            fix_coordinates_for_bc_import(location_dict, coordinates)

        command = (
            "bc-import {location_to_be_imported} {pos_x} {pos_y} {pos_z}"
        ).format(
            location_to_be_imported=location_dict.get("identifier"),
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
    "description": "imports a saved prefab. Needs to have a location first!",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
