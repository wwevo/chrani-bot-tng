from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def send_player_update_to_map(*args, **kwargs):
    """Send player updates to map view via socket.io"""
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", {})

    if updated_values_dict is None:
        return

    # Get steamid and dataset
    steamid = updated_values_dict.get("steamid")
    dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    if not all([dataset, steamid]):
        return

    # Get full player data from DOM
    player_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(dataset, {})
        .get(steamid, {})
    )

    if not player_dict:
        return

    # Check which clients are viewing the map
    for clientid in module.webserver.connected_clients.keys():
        current_view = module.get_current_view(clientid)
        if current_view != "map":
            continue

        # Prepare player update data
        pos = player_dict.get("pos", {})
        if not pos:
            continue

        player_update_data = {
            "steamid": steamid,
            "name": player_dict.get("name", "Player"),
            "level": player_dict.get("level", 0),
            "health": player_dict.get("health", 0),
            "zombies": player_dict.get("zombies", 0),
            "deaths": player_dict.get("deaths", 0),
            "players": player_dict.get("players", 0),
            "score": player_dict.get("score", 0),
            "ping": player_dict.get("ping", 0),
            "is_muted": player_dict.get("is_muted", False),
            "is_authenticated": player_dict.get("is_authenticated", False),
            "in_limbo": player_dict.get("in_limbo", False),
            "is_initialized": player_dict.get("is_initialized", False),
            "permission_level": player_dict.get("permission_level", None),
            "dataset": dataset,
            "position": {
                "x": float(pos.get("x", 0)),
                "y": float(pos.get("y", 0)),
                "z": float(pos.get("z", 0))
            }
        }

        module.webserver.send_data_to_client_hook(
            module,
            payload=player_update_data,
            data_type="player_position_update",
            clients=[clientid]
        )


trigger_meta = {
    "description": "sends player updates to webmap clients",
    "main_function": send_player_update_to_map,
    "handlers": {
        # Listen to all player field updates that are relevant for the map
        "module_players/elements/%map_identifier%/%steamid%/pos": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/health": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/level": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/zombies": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/deaths": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/players": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/score": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/ping": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/is_muted": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/is_authenticated": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/in_limbo": send_player_update_to_map,
        "module_players/elements/%map_identifier%/%steamid%/is_initialized": send_player_update_to_map,
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
