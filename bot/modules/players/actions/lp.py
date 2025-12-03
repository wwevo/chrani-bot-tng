from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_SHORT, TELNET_PREFIXES
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)

    return

    timeout = TELNET_TIMEOUT_SHORT
    timeout_start = time()
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = []

    if module.telnet.add_telnet_command_to_queue("lp"):
        poll_is_finished = False
        regex = action_meta.get("regex")[0]


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


def callback_success(module, action_meta, dispatchers_id, match=None):
    return

    """ without a place to store this, why bother """
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_count = int(match.group("player_count"))
    if all([
        active_dataset is None,
        player_count <= 0
    ]):
        return False

    """ lets extract all data the game provides!! """
    raw_playerdata = match.group("raw_playerdata").lstrip()
    regex = action_meta.get("regex")[1]


    all_players_dict = (
        module.dom.data.get(module.get_module_identifier(), {})
        .get(active_dataset, {})
        .get("elements", {})
    )

    players_to_update_dict = {}
    for m in re.finditer(regex, raw_playerdata):
        in_limbo = int(m.group("health")) == 0
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
            "owner": m.group("steamid")
        }
        players_to_update_dict[m.group("steamid")] = player_dict

    """ players_to_update_dict now holds all game-data for all online players plus a few generated ones like last seen
    and is_initialized. Otherwise it's empty """

    # set all players not currently online to offline
    online_players_list = list(players_to_update_dict.keys())
    for steamid, existing_player_dict in all_players_dict.items():
        print(existing_player_dict)
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
                active_dataset: {
                    "elements": players_to_update_dict
                }
            }
        })

    if online_players_list != module.dom.data.get(module.get_module_identifier(), {}).get("online_players"):
        module.dom.data.upsert({
            module.get_module_identifier(): {
                "online_players": online_players_list
            }
        })


def callback_skip(module, action_meta, dispatchers_id=None):
    return

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        return

    all_existing_players_dict = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get(active_dataset, {})
        .get("elements", {})
    )

    # Mark all existing players as offline using helper function
    all_modified_players_dict = _set_players_offline(all_existing_players_dict)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            active_dataset: {
                "elements": all_modified_players_dict
            }
        }
    })


def callback_fail(module, action_meta, dispatchers_id=None):
    return

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        return

    all_existing_players_dict = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get(active_dataset, {})
        .get("elements", {})
    )

    # Mark all existing players as offline using helper function
    all_modified_players_dict = _set_players_offline(all_existing_players_dict)

    module.dom.data.upsert({
        module.get_module_identifier(): {
            active_dataset: {
                "elements": all_modified_players_dict
            }
        }
    })

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "online_players": []
        }
    })

def _set_players_offline(players_dict):
    modified_players = {}
    for steam_id, player_data in players_dict.items():
        # Create a copy of the player dict
        updated_player = player_data.copy()
        updated_player["is_online"] = False
        updated_player["is_initialized"] = False
        modified_players[steam_id] = updated_player

    return modified_players


action_meta = {
    "id": action_name,
    "description": "gets a list of all currently logged in players and sets status-flags",
    "main_function": main_function,
    "callbacks": {
        "callback_success": callback_success,
        "callback_fail": callback_fail,
        "callback_skip": callback_skip,
    },
    "parameters": {
        "periodic": True,
        "requires_telnet_connection": True,
        "enabled": True
    },
    "regex": [
        (
            TELNET_PREFIXES["telnet_log"]["timestamp"] +
            r"Executing\scommand\s\'lp\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
            r"(?P<raw_playerdata>[\s\S]*?)Total\sof\s(?P<player_count>\d{1,2})\sin\sthe\sgame"
        ),
        (
            r"\d{1,2}\. id=(?P<id>\d+), (?P<name>[^,]+), "
            r"pos=\((?P<pos_x>-?\d+\.\d+), (?P<pos_y>-?\d+\.\d+), (?P<pos_z>-?\d+\.\d+)\), "
            r"rot=\((?P<rot_x>-?\d+\.\d+), (?P<rot_y>-?\d+\.\d+), (?P<rot_z>-?\d+\.\d+)\), "
            r"remote=(?P<remote>\w+), "
            r"health=(?P<health>\d+), "
            r"deaths=(?P<deaths>\d+), "
            r"zombies=(?P<zombies>\d+), "
            r"players=(?P<players>\d+), "
            r"score=(?P<score>\d+), "
            r"level=(?P<level>\d+), "
            r"pltfmid=Steam_(?P<steamid>\d+), crossid=(?P<crossid>[\w_]+), "
            r"ip=(?P<ip>[^,]+), "
            r"ping=(?P<ping>\d+)"
            r"\r\n"
        )
    ]
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
