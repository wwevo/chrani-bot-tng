from bot import loaded_modules_dict
from os import path, pardir
from datetime import datetime

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    """
    Injects telnet lines to simulate a player joining the game.

    This generates the correct telnet line format for:
    - Player entering multiplayer (EnterMultiplayer)
    - Player joining multiplayer (JoinMultiplayer)
    - Player spawning in world

    Event data format:
    {
        'steamid': str,       # Player's SteamID (optional, auto-generated if missing)
        'name': str,          # Player name (optional, defaults to "TestPlayer")
        'entity_id': int,     # Entity ID (optional, auto-generated)
        'pos': {              # Spawn position (optional, defaults to 0,50,0)
            'x': int,
            'y': int,
            'z': int
        }
    }
    """
    event_data[1]["action_identifier"] = action_name

    # Get or generate player data
    steamid = event_data[1].get("steamid", None)
    if steamid is None:
        # Auto-generate test SteamID
        test_prefix = module.options.get("test_steamid_prefix", "76561198999")
        # Use current injection count as unique ID
        count = module.dom.data.get(module.get_module_identifier(), {}).get("injection_count", 0)
        steamid = f"{test_prefix}{str(count).zfill(6)}"

    player_name = event_data[1].get("name", f"TestPlayer_{steamid[-6:]}")
    entity_id = event_data[1].get("entity_id", 1000 + (int(steamid[-6:]) if steamid[-6:].isdigit() else 1000))

    # Get spawn position
    pos = event_data[1].get("pos", {"x": 0, "y": 50, "z": 0})

    # Generate timestamp (current time in game format)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    stardate = "1000.000"  # Dummy stardate value

    # Generate telnet lines for player join sequence
    telnet_lines = []

    # Line 1: PlayerSpawnedInWorld (EnterMultiplayer) - First time joining
    telnet_lines.append(
        f"{timestamp} {stardate} INF PlayerSpawnedInWorld "
        f"(reason: EnterMultiplayer, position: {pos['x']}, {pos['y']}, {pos['z']}): "
        f"EntityID={entity_id}, PlayerID='{steamid}', OwnerID='{steamid}', PlayerName='{player_name}'"
    )

    # Line 2: PlayerSpawnedInWorld (JoinMultiplayer) - Subsequent joins
    telnet_lines.append(
        f"{timestamp} {stardate} INF PlayerSpawnedInWorld "
        f"(reason: JoinMultiplayer, position: {pos['x']}, {pos['y']}, {pos['z']}): "
        f"EntityID={entity_id}, PlayerID='{steamid}', OwnerID='{steamid}', PlayerName='{player_name}'"
    )

    # Line 3: GMSG - Join message
    telnet_lines.append(
        f"{timestamp} {stardate} INF GMSG: Player '{player_name}' joined the game"
    )

    # Inject all lines using inject_telnet_line action
    for telnet_line in telnet_lines:
        inject_event_data = ['inject_telnet_line', {
            'line': telnet_line
        }]
        module.trigger_action_hook(module, event_data=inject_event_data)

    # Store the generated data for reference
    event_data[1]["generated_steamid"] = steamid
    event_data[1]["generated_name"] = player_name
    event_data[1]["generated_entity_id"] = entity_id

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_name = event_data[1].get("generated_name", "unknown")
    steamid = event_data[1].get("generated_steamid", "unknown")
    print(f"[Testing] Simulated player join: {player_name} ({steamid})")


def callback_fail(module, event_data, dispatchers_steamid):
    fail_reason = event_data[1].get("fail_reason", "unknown error")
    print(f"[Testing] Failed to simulate player join: {fail_reason}")


action_meta = {
    "description": "Simulates a player joining the game",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
