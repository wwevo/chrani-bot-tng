from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_SHORT
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def _set_players_offline(players_dict):
    """
    Helper function to mark all players in a dictionary as offline.

    Creates a new dictionary with all players set to is_online=False and
    is_initialized=False. This is used when telnet commands fail or timeout.

    Args:
        players_dict: Dictionary of player data keyed by steam_id

    Returns:
        Dictionary with same players but marked as offline
    """
    modified_players = {}
    for steam_id, player_data in players_dict.items():
        # Create a copy of the player dict
        updated_player = player_data.copy()
        updated_player["is_online"] = False
        updated_player["is_initialized"] = False
        modified_players[steam_id] = updated_player

    return modified_players


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = TELNET_TIMEOUT_SHORT
    timeout_start = time()
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    if module.telnet.add_telnet_command_to_queue("lp"):
        poll_is_finished = False
        regex = (
            r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
            r"Executing\scommand\s\'lp\'\sby\sTelnet\sfrom\s"
            r"(?P<called_by>.*)(?P<raw_playerdata>[\s\S]+?)Total\sof\s(?P<player_count>\d{1,2})\sin\sthe\sgame"
        )

        while not poll_is_finished and (time() < timeout_start + timeout):
            sleep(0.25)
            match = False
            for match in re.finditer(regex, module.telnet.telnet_buffer):
                poll_is_finished = True

            if match:
                module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
                return

        event_data[1]["fail_reason"].append("timed out waiting for response")
    else:
        event_data[1]["fail_reason"].append("action already queued up")

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    """ without a place to store this, why bother """
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_count = int(match.group("player_count"))
    if all([
        active_dataset is None,
        player_count <= 0
    ]):
        return False

    """ get some basic stuff needed later """
    last_seen_gametime_string = module.game_environment.get_last_recorded_gametime_string()

    """ lets extract all data the game provides!! """
    telnet_datetime = match.group("datetime")
    raw_playerdata = match.group("raw_playerdata").lstrip()
    regex = (
        r"\d{1,2}. id=(?P<id>\d+), (?P<name>.+), "
        r"pos=\((?P<pos_x>.?\d+.\d), (?P<pos_y>.?\d+.\d), (?P<pos_z>.?\d+.\d)\), "
        r"rot=\((?P<rot_x>.?\d+.\d), (?P<rot_y>.?\d+.\d), (?P<rot_z>.?\d+.\d)\), "
        r"remote=(?P<remote>\w+), "
        r"health=(?P<health>\d+), "
        r"deaths=(?P<deaths>\d+), "
        r"zombies=(?P<zombies>\d+), "
        r"players=(?P<players>\d+), "
        r"score=(?P<score>\d+), "
        r"level=(?P<level>\d+), "
        r"steamid=(?P<steamid>\d+), "
        r"ip=(?P<ip>.*), "
        r"ping=(?P<ping>\d+)"
        r"\r\n"
    )

    all_players_dict = (
        module.dom.data.get(module.get_module_identifier(), {})
        .get("elements", {})
        .get(active_dataset, {})
    )

    players_to_update_dict = {}
    for m in re.finditer(regex, raw_playerdata):
        in_limbo = True if int(m.group("health")) == 0 else False
        player_dict = {
            # data the game provides
            "id": m.group("id"),
            "name": str(m.group("name")),
            "remote": bool(m.group("remote")),
            "health": int(m.group("health")),
            "deaths": int(m.group("deaths")),
            "zombies": int(m.group("zombies")),
            "players": int(m.group("players")),
            "score": int(m.group("score")),
            "level": int(m.group("level")),
            "steamid": m.group("steamid"),
            "ip": str(m.group("ip")),
            "ping": int(float(m.group("ping"))),
            "pos": {
                "x": int(float(m.group("pos_x"))),
                "y": int(float(m.group("pos_y"))),
                "z": int(float(m.group("pos_z")))
            },
            "rot": {
                "x": int(float(m.group("rot_x"))),
                "y": int(float(m.group("rot_y"))),
                "z": int(float(m.group("rot_z")))
            },
            # data invented by the bot
            "dataset": active_dataset,
            "in_limbo": in_limbo,
            "is_online": True,
            "is_initialized": True,
            "last_updated_servertime": telnet_datetime,
            "last_seen_gametime": last_seen_gametime_string,
            "owner": m.group("steamid")
        }
        players_to_update_dict[m.group("steamid")] = player_dict

    """ players_to_update_dict now holds all game-data for all online players plus a few generated ones like last seen
    and is_initialized. Otherwise it's empty """

    # set all players not currently online to offline
    online_players_list = list(players_to_update_dict.keys())
    for steamid, existing_player_dict in all_players_dict.items():
        if existing_player_dict["is_initialized"] is False:
            continue

        if steamid not in online_players_list and existing_player_dict["is_online"] is True:
            # Create offline version of player using copy
            updated_player = existing_player_dict.copy()
            updated_player["is_online"] = False
            updated_player["is_initialized"] = False
            players_to_update_dict[steamid] = updated_player

    if len(players_to_update_dict) >= 1:
        module.dom.data.upsert({
            module.get_module_identifier(): {
                "elements": {
                    active_dataset: players_to_update_dict
                }
            }
        })

    if online_players_list != module.dom.data.get(module.get_module_identifier(), {}).get("online_players"):
        module.dom.data.upsert({
            module.get_module_identifier(): {
                "online_players": online_players_list
            }
        })


def callback_fail(module, event_data, dispatchers_steamid):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        return

    all_existing_players_dict = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get("elements", {})
        .get(active_dataset, {})
    )

    # Mark all existing players as offline using helper function
    all_modified_players_dict = _set_players_offline(all_existing_players_dict)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "elements": {
                active_dataset: all_modified_players_dict
            }
        }
    })

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "online_players": []
        }
    })


def skip_it(module, event_data, dispatchers_steamid=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        return

    all_existing_players_dict = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get("elements", {})
        .get(active_dataset, {})
    )

    # Mark all existing players as offline using helper function
    all_modified_players_dict = _set_players_offline(all_existing_players_dict)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "elements": {
                active_dataset: all_modified_players_dict
            }
        }
    })


action_meta = {
    "description": "gets a list of all currently logged in players and sets status-flags",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "skip_it": skip_it,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
