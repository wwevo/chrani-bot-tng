from bot import loaded_modules_dict
from bot.logger import get_logger
from os import path, pardir
from time import time

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]
logger = get_logger("players.teleport_player")


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 8  # [seconds] - increased for event-based handling
    event_data[1]["action_identifier"] = action_name

    target_coordinates = event_data[1].get("coordinates", None)
    player_to_be_teleported_steamid = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_to_be_teleported_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(dataset, {})
        .get(player_to_be_teleported_steamid, {})
    )
    player_coordinates = player_to_be_teleported_dict.get("pos", None)

    if all([
        dataset is not None,
        target_coordinates is not None,
        player_coordinates is not None
    ]) and all([
        # no sense in porting a player to a place they are already standing on ^^
        target_coordinates != player_coordinates
    ]):
        # Check if player is online before attempting teleport
        if player_to_be_teleported_dict.get("is_online", False) is False:
            event_data[1]["fail_reason"] = "player is not online"
            module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
            return

        # Use entity ID instead of steamid - game requires entity ID now
        player_entity_id = player_to_be_teleported_dict.get("id")
        if not player_entity_id:
            event_data[1]["fail_reason"] = "player entity ID not found"
            module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
            return

        # Per-player lock: Check if teleport is already pending for this player
        if player_to_be_teleported_steamid in module.pending_teleports:
            event_data[1]["fail_reason"] = "teleport already pending for this player"
            logger.warn("teleport_blocked_already_pending",
                       steamid=player_to_be_teleported_steamid,
                       user=dispatchers_steamid)
            module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
            return

        # Use -1 for Y coordinate if unclear/null (gameserver normalizes to ground level)
        raw_y = int(float(target_coordinates["y"]))
        pos_y = -1 if raw_y <= 0 else raw_y
        
        command = (
            "teleportplayer {player_to_be_teleported} {pos_x} {pos_y} {pos_z}"
        ).format(
            player_to_be_teleported=player_entity_id,
            pos_x=int(float(target_coordinates["x"])),
            pos_y=pos_y,
            pos_z=int(float(target_coordinates["z"]))
        )

        if not module.telnet.add_telnet_command_to_queue(command):
            event_data[1]["fail_reason"] = "duplicate command"
            module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
            return

        # Event-based handling: Register pending teleport
        # Completion will be handled by playerspawn trigger when PlayerSpawnedInWorld arrives
        module.pending_teleports[player_to_be_teleported_steamid] = {
            "entity_id": player_entity_id,
            "target_pos": target_coordinates,
            "timestamp": time(),
            "timeout": timeout,
            "callback_success": callback_success,
            "callback_fail": callback_fail,
            "event_data": event_data,
            "dispatchers_steamid": dispatchers_steamid
        }
        
        logger.debug("teleport_registered_pending",
                    steamid=player_to_be_teleported_steamid,
                    entity_id=player_entity_id,
                    target_pos=target_coordinates,
                    user=dispatchers_steamid)
        
        # Return immediately - no blocking!
        # Success/failure will be handled by:
        # - playerspawn trigger (on success)
        # - timeout watcher in players module run loop (on timeout)
        return

    event_data[1]["fail_reason"] = "insufficient data for execution"
    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
    return


def callback_success(module, event_data, dispatchers_steamid, match=None):
    player_to_be_teleported = event_data[1].get("steamid", None)
    dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)


def callback_fail(module, event_data, dispatchers_steamid):
    logger.error("teleport_failed",
                user=dispatchers_steamid,
                target=event_data[1].get("steamid"),
                reason=event_data[1].get("fail_reason", "no reason known"))


action_meta = {
    "description": "teleports a player",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
