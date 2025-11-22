from .discord_webhook import DiscordWebhook
from bot import loaded_modules_dict
from bot import telnet_prefixes
from bot.logger import get_logger
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]
logger = get_logger("players.playerspawn")


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    update_player_pos = False
    last_recorded_gametime_string = module.game_environment.get_last_recorded_gametime_string()

    if command == "joined the game":
        player_name = regex_result.group("player_name")
        payload = '{} joined {} at {}'.format(player_name, active_dataset, last_recorded_gametime_string)

        discord_payload_url = origin_module.options.get("discord_webhook", None)
        if discord_payload_url is not None:
            webhook = DiscordWebhook(
                url=discord_payload_url,
                content=payload
            )
            webhook.execute()

    elif any([
        command == "EnterMultiplayer",
        command == "JoinMultiplayer"
    ]):
        steamid = regex_result.group("player_steamid")
        player_name = regex_result.group("player_name")
        existing_player_dict = (
            module.dom.data.get("module_players", {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(steamid, {})
        )

        player_dict = {
            "name": player_name
        }
        player_dict.update(existing_player_dict)

        if command == "EnterMultiplayer":
            player_dict["first_seen_gametime"] = last_recorded_gametime_string
            module.dom.data.upsert({
                "module_players": {
                    "elements": {
                        active_dataset: {
                            steamid: player_dict
                        }
                    }
                }
            })
        elif command == "JoinMultiplayer":
            default_player_password = module.default_options.get("default_player_password", None)
            if player_dict.get("is_authenticated", False) is True or default_player_password is None:
                message = "[66FF66]Welcome back[-] [FFFFFF]{}[-]".format(player_name)
            else:
                message = (
                    "[66FF66]Welcome to the server[-] [FFFFFF]{player_name}[-]"
                ).format(
                    player_name=player_name
                )
                if default_player_password is not None:
                    message += ", [FF6666]please authenticate[-] [FFFFFF]and make yourself at home[-]"

            event_data = ['say_to_player', {
                'steamid': steamid,
                'message': message
            }]
            module.trigger_action_hook(origin_module.players, event_data=event_data)
    elif command == "Teleport":
        update_player_pos = True
        
        # Check if this teleport was pending (event-based completion)
        player_steamid = regex_result.group("player_steamid")
        
        # Access players module (not origin_module which might be game_environment)
        players_module = loaded_modules_dict.get("module_players")
        if players_module is None:
            logger.error("teleport_callback_players_module_not_found", steamid=player_steamid)
            return
        
        pending_teleport = players_module.pending_teleports.get(player_steamid)
        
        if pending_teleport:
            # Teleport succeeded - trigger success callback
            callback_success = pending_teleport.get("callback_success")
            event_data = pending_teleport.get("event_data")
            dispatchers_steamid = pending_teleport.get("dispatchers_steamid")
            
            if callback_success and event_data:
                try:
                    # Pass the correct module (players_module) to callback
                    callback_success(players_module, event_data, dispatchers_steamid, regex_result)
                    logger.debug("teleport_success_callback_triggered", steamid=player_steamid)
                except Exception as e:
                    logger.error("teleport_success_callback_failed",
                               steamid=player_steamid,
                               error=str(e),
                               error_type=type(e).__name__)
            
            # Remove from pending registry
            del players_module.pending_teleports[player_steamid]
            logger.debug("teleport_completed_removed_from_pending", steamid=player_steamid)

    if update_player_pos:
        player_to_be_updated = regex_result.group("player_steamid")
        pos_after_teleport = {
            "pos": {
                "x": regex_result.group("pos_x"),
                "y": regex_result.group("pos_y"),
                "z": regex_result.group("pos_z"),
            }
        }
        # update the players location data with the teleport ones
        module.dom.data.upsert({
            "module_players": {
                "elements": {
                    active_dataset: {
                        player_to_be_updated: pos_after_teleport
                    }
                }
            }
        })


trigger_meta = {
    "description": "reacts to telnets playerspawn messages for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                r"PlayerSpawnedInWorld\s"
                r"\("
                r"reason: (?P<command>.+?),\s"
                r"position: (?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)"
                r"\):\s"
                r"EntityID=(?P<entity_id>.*),\s"
                r"PltfmId='Steam_(?P<player_steamid>.*)',\s"
                r"CrossId='(?P<cross_id>[^']+)',\s"
                r"OwnerID='(?P<owner_steamid>[^']+)',\s"
                r"PlayerName='(?P<player_name>[^']+)',\s"
                r"ClientNumber='(?P<client_number>[^']+)'"
            ),
            "callback": main_function
        }, {
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                r"Player (?P<command>.*): "
                r"EntityID=(?P<entity_id>.*), "
                r"PltfmId='Steam_(?P<player_steamid>.*)', "
                r"CrossId='(?P<cross_id>[^']+)', "
                r"OwnerID='(?P<owner_id>[^']+)', "
                r"PlayerName='(?P<player_name>[^']+)'$"
            ),
            "callback": main_function
        }, {
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                telnet_prefixes["GMSG"]["command"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
