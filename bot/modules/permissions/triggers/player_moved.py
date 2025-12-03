from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, **kwargs):
    print(trigger_name, ": ", module)
    print(kwargs)

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if not active_dataset:
        print("pass: no active dataset to work with")
        return

    original_data = kwargs.get("original_data", {})
    updated_data = kwargs.get("updated_data", {})

    # only dive into this when not authenticated
    if original_data.get("is_authenticated"):
        print("pass: authenticated player")
        return

    found_enabled_lobby = False
    for lobby_dict in module.locations.get_elements_by_type("is_lobby"):
        # TODO: if more than one lobby, what to do?
        if lobby_dict.get("enabled"):
            found_enabled_lobby = True

    if not found_enabled_lobby:
        print("pass: no enabled lobby found")
        return

    on_the_move_player_dict = (
        module.dom.data
        .get("module_players", {})
        .get(active_dataset, {})
        .get("elements", {})
        .get(updated_data.get("steamid"), {})
    )

    # Prevent race conditions: Don't teleport players who are disconnecting
    if on_the_move_player_dict.get("is_online", False) is False:
        return

    # Prevent feedback loop: Don't teleport if already pending
    player_steamid = on_the_move_player_dict.get("steamid")
    if player_steamid in module.players.pending_teleports:
        return

    pos_is_inside_coordinates = module.locations.position_is_inside_boundary(updated_data, lobby_dict)
    if pos_is_inside_coordinates is True:
        # nothing to do, we are inside the lobby
        return

    # no early exits, seems like the player is outside an active lobby without any authentication!
    # seems like we should port ^^

    # Use teleport_entry if available, otherwise fall back to lobby coordinates
    teleport_entry = lobby_dict.get("teleport_entry", {})
    teleport_x = teleport_entry.get("x")
    teleport_y = teleport_entry.get("y")
    teleport_z = teleport_entry.get("z")

    # If teleport_entry is not set or is (0,0,0), use lobby coordinates
    if any([
        teleport_x is None,
        teleport_y is None,
        teleport_z is None,
        all([
            int(float(teleport_x)) == 0,
            int(float(teleport_y)) == 0,
            int(float(teleport_z)) == 0,
        ])
    ]):
        teleport_coords = {
            "x": lobby_dict["coordinates"]["x"],
            "y": lobby_dict["coordinates"]["y"],
            "z": lobby_dict["coordinates"]["z"]
        }
    else:
        teleport_coords = {
            "x": teleport_x,
            "y": teleport_y,
            "z": teleport_z
        }

    event_data = ['teleport_to_coordinates', {
        'location_coordinates': teleport_coords,
        'steamid': player_steamid
    }]
    module.trigger_action_hook(module.locations, event_data=event_data)


trigger_meta = {
    "description": "reacts to every players move!",
    "main_function": main_function,
    "handlers": {
        "module_players/%dataset%/elements/%steamid%/pos": main_function,
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
