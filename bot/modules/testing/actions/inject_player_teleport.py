from bot import loaded_modules_dict
from os import path, pardir
from datetime import datetime

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    """
    Injects a telnet line to simulate a player teleporting.

    This updates the player's position in the DOM immediately.

    Event data format:
    {
        'steamid': str,  # Player's SteamID (required)
        'pos': {         # Target position (required)
            'x': int,
            'y': int,
            'z': int
        }
    }
    """
    event_data[1]["action_identifier"] = action_name

    steamid = event_data[1].get("steamid", None)
    pos = event_data[1].get("pos", None)

    if steamid is None or pos is None:
        event_data[1]["fail_reason"] = "missing steamid or position"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    # Get player data from DOM to get entity_id and name
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", "TestWorld_Default")
    player_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(steamid, {})
    )

    entity_id = player_dict.get("id", event_data[1].get("entity_id", 1000))
    player_name = player_dict.get("name", f"TestPlayer_{steamid[-6:]}")

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    stardate = "1000.000"

    # Generate PlayerSpawnedInWorld telnet line with Teleport reason
    telnet_line = (
        f"{timestamp} {stardate} INF PlayerSpawnedInWorld "
        f"(reason: Teleport, position: {pos['x']}, {pos['y']}, {pos['z']}): "
        f"EntityID={entity_id}, PlayerID='{steamid}', OwnerID='{steamid}', PlayerName='{player_name}'"
    )

    # Inject the line
    inject_event_data = ['inject_telnet_line', {
        'line': telnet_line
    }]
    module.trigger_action_hook(module, event_data=inject_event_data)

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    steamid = event_data[1].get("steamid", "unknown")
    pos = event_data[1].get("pos", {})
    print(f"[Testing] Simulated player teleport: {steamid} to {pos}")


def callback_fail(module, event_data, dispatchers_steamid):
    fail_reason = event_data[1].get("fail_reason", "unknown error")
    print(f"[Testing] Failed to simulate player teleport: {fail_reason}")


action_meta = {
    "description": "Simulates a player teleporting to coordinates",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
