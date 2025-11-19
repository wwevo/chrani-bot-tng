from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    """
    Cleans up all test data based on naming conventions.

    This removes:
    - Players with SteamIDs matching test_steamid_prefix (default: 76561198999)
    - Locations with identifiers matching test_location_prefix (default: test_)
    - Datasets matching test_dataset_prefix (default: TestWorld_)

    Event data format:
    {
        'confirm': bool  # Safety flag, must be True to execute
    }
    """
    event_data[1]["action_identifier"] = action_name

    # Safety check
    if not event_data[1].get("confirm", False):
        event_data[1]["fail_reason"] = "cleanup not confirmed (set 'confirm': true)"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    # Get naming prefixes from options
    test_steamid_prefix = module.options.get("test_steamid_prefix", "76561198999")
    test_location_prefix = module.options.get("test_location_prefix", "test_")
    test_dataset_prefix = module.options.get("test_dataset_prefix", "TestWorld_")

    cleanup_stats = {
        "players_removed": 0,
        "locations_removed": 0,
        "datasets_removed": 0
    }

    # Clean up test players
    players_data = module.dom.data.get("module_players", {}).get("elements", {})
    for dataset_name, player_dicts in list(players_data.items()):
        for steamid, player_dict in list(player_dicts.items()):
            if steamid.startswith(test_steamid_prefix):
                # Remove this test player
                module.dom.data.remove_key_by_path(
                    ["module_players", "elements", dataset_name, steamid],
                    dispatchers_steamid=dispatchers_steamid
                )
                cleanup_stats["players_removed"] += 1
                print(f"[Testing] Removed test player: {player_dict.get('name', steamid)}")

    # Clean up test locations
    locations_data = module.dom.data.get("module_locations", {}).get("elements", {})
    for dataset_name, owner_dicts in list(locations_data.items()):
        for owner_steamid, location_dicts in list(owner_dicts.items()):
            for location_id, location_dict in list(location_dicts.items()):
                if location_id.startswith(test_location_prefix):
                    # Remove this test location
                    module.dom.data.remove_key_by_path(
                        ["module_locations", "elements", dataset_name, owner_steamid, location_id],
                        dispatchers_steamid=dispatchers_steamid
                    )
                    cleanup_stats["locations_removed"] += 1
                    print(f"[Testing] Removed test location: {location_dict.get('name', location_id)}")

    # Clean up test datasets (if entire dataset is test data)
    # Players datasets
    for dataset_name in list(players_data.keys()):
        if dataset_name.startswith(test_dataset_prefix):
            module.dom.data.remove_key_by_path(
                ["module_players", "elements", dataset_name],
                dispatchers_steamid=dispatchers_steamid
            )
            cleanup_stats["datasets_removed"] += 1
            print(f"[Testing] Removed test dataset from players: {dataset_name}")

    # Locations datasets
    for dataset_name in list(locations_data.keys()):
        if dataset_name.startswith(test_dataset_prefix):
            module.dom.data.remove_key_by_path(
                ["module_locations", "elements", dataset_name],
                dispatchers_steamid=dispatchers_steamid
            )
            print(f"[Testing] Removed test dataset from locations: {dataset_name}")

    # Game environment datasets
    game_env_data = module.dom.data.get("module_game_environment", {})
    for dataset_name in list(game_env_data.keys()):
        if dataset_name.startswith(test_dataset_prefix) and dataset_name != "active_dataset":
            module.dom.data.remove_key_by_path(
                ["module_game_environment", dataset_name],
                dispatchers_steamid=dispatchers_steamid
            )
            print(f"[Testing] Removed test dataset from game_environment: {dataset_name}")

    # Store cleanup stats
    event_data[1]["cleanup_stats"] = cleanup_stats

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    stats = event_data[1].get("cleanup_stats", {})
    print(f"[Testing] Cleanup complete: {stats['players_removed']} players, "
          f"{stats['locations_removed']} locations, {stats['datasets_removed']} datasets removed")


def callback_fail(module, event_data, dispatchers_steamid):
    fail_reason = event_data[1].get("fail_reason", "unknown error")
    print(f"[Testing] Cleanup failed: {fail_reason}")


action_meta = {
    "description": "Cleans up all test data based on naming conventions",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
