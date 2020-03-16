from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 2  # [seconds]
    timeout_start = time()

    if not module.telnet.add_telnet_command_to_queue("lp"):
        # module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    poll_is_finished = False
    regex = (
        r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
        r"Executing\scommand\s\'lp\'\sby\sTelnet\sfrom\s"
        r"(?P<called_by>.*)(?P<raw_playerdata>[\s\S]+?)Total\sof\s(?P<player_count>\d{1,2})\sin\sthe\sgame"
    )

    player_count = 0
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer):
            poll_is_finished = True

        if match:
            module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)
            return

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
    last_recorded_gametime = (
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("last_recorded_gametime", {})
    )
    last_seen_gametime_string = "Day {day}, {hour}:{minute}".format(
        day=last_recorded_gametime.get("day", {}),
        hour=last_recorded_gametime.get("hour", {}),
        minute=last_recorded_gametime.get("minute", {})
    )

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
            player_dict = {}
            player_dict.update(existing_player_dict)

            player_dict["is_online"] = False
            player_dict["is_initialized"] = False

            players_to_update_dict.update({
                steamid: player_dict
            })

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

    all_modified_players_dict = {}
    for steamid, existing_player_dict in all_existing_players_dict.items():
        player_dict = {}
        player_dict.update(existing_player_dict)
        player_dict["is_online"] = False
        player_dict["is_initialized"] = False

        all_modified_players_dict.update({steamid: player_dict})

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

    all_modified_players_dict = {}
    for steamid, existing_player_dict in all_existing_players_dict.items():
        player_dict = {}
        player_dict.update(existing_player_dict)
        player_dict["is_online"] = False
        player_dict["is_initialized"] = False
        all_modified_players_dict.update({steamid: player_dict})

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
