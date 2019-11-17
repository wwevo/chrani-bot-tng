from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(*args, **kwargs):
    module = args[0]
    original_values_dict = kwargs.get("original_values_dict", {})
    updated_values_dict = kwargs.get("updated_values_dict", {})

    try:
        if any([
            original_values_dict.get("pos", {}).get("x") != updated_values_dict.get("pos", {}).get("x"),
            original_values_dict.get("pos", {}).get("y") != updated_values_dict.get("pos", {}).get("y"),
            original_values_dict.get("pos", {}).get("z") != updated_values_dict.get("pos", {}).get("z")
        ]):
            current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)

            lobby_dict = (
                module.dom.data
                .get("module_locations", {})
                .get("elements", {})
                .get(current_map_identifier, {})
                .get("76561198040658370", {})
                .get("Lobby", {})
            )
            if all([
                not module.locations.position_is_inside_boundary(updated_values_dict, lobby_dict),
                original_values_dict.get("is_authenticated", False) is False
            ]):
                event_data = ['management_tools', {
                    'location_coordinates': {
                        "x": lobby_dict["coordinates"]["x"],
                        "y": lobby_dict["coordinates"]["y"],
                        "z": lobby_dict["coordinates"]["z"]
                    },
                    'action': 'teleport'
                }]
                module.trigger_action_hook(module.locations, event_data, original_values_dict.get("steamid"))

            return

    except AttributeError:
        pass


trigger_meta = {
    "description": "reacts to every players move!",
    "main_function": main_function,
    "handlers": {
        "module_players/elements/%map_identifier%/%steamid%/pos": main_function,
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
