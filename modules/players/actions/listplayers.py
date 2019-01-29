from modules import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def reset_and_update_live_status(module, player_dict):
    online_players_list = module.dom.data.get("module_environment", {}).get("online_players_list", [])
    if player_dict["steamid"] in online_players_list:
        online_players_list.remove(player_dict["steamid"])
    module.dom.data[module.get_module_identifier()]["online_players_list"] = online_players_list
    module.dom.data[module.get_module_identifier()]["players"][player_dict["steamid"]]["is_online"] = False
    module.dom.data[module.get_module_identifier()]["players"][player_dict["steamid"]]["ping"] = "offline"
    module.update_player_table_widget_table_row(player_dict)


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 1.5  # [seconds]
    timeout_start = time()

    module.telnet.add_telnet_command_to_queue("lp")
    poll_is_finished = False
    regex = (
        r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
        r"Executing\scommand\s\'lp\'\sby\sTelnet\sfrom\s"
        r"(?P<called_by>.*)(?P<raw_playerdata>[\s\S]+?)Total\sof\s(?P<playercount>\d{1,2})\sin\sthe\sgame"
    )
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer):
            telnet_datetime = match.group("datetime")
            poll_is_finished = True

        if match:
            callback_success(module, event_data, dispatchers_steamid, match, telnet_datetime)
            return

    callback_fail(module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match, telnet_datetime):
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
    all_players_dict = module.dom.data.get(module.get_module_identifier(), {}).get("players", {})
    online_players = []
    for m in re.finditer(regex, raw_playerdata):
        in_limbo = True if int(m.group("health")) == 0 else False
        online_players.append(m.group("steamid"))
        player_dict = {
            "id": m.group("id"),
            "name": str(m.group("name")),
            "pos": {
                "x": float(m.group("pos_x")),
                "y": float(m.group("pos_y")),
                "z": float(m.group("pos_z")),
            },
            "rot": {
                "x": float(m.group("rot_x")),
                "y": float(m.group("rot_y")),
                "z": float(m.group("rot_z")),
            },
            "remote": bool(m.group("remote")),
            "health": int(m.group("health")),
            "deaths": int(m.group("deaths")),
            "zombies": int(m.group("zombies")),
            "players": int(m.group("players")),
            "score": m.group("score"),
            "level": m.group("level"),
            "steamid": m.group("steamid"),
            "ip": str(m.group("ip")),
            "ping": int(m.group("ping")),
            "in_limbo": in_limbo,
            "is_online": True,
            "last_updated": telnet_datetime
        }
        if not all_players_dict.get(m.group("steamid"), {}).get("is_online", False):
            module.update_player_table_widget_table_row(player_dict)
        else:
            module.update_player_table_widget_data(player_dict)

        module.dom.upsert({
            module.get_module_identifier(): {
                "players": {
                    m.group("steamid"): player_dict
                }
            }
        })

    for steamid, player_dict in all_players_dict.items():
        if steamid == 'last_updated':
            continue

        if any([
            not module.dom.data.get(module.telnet.get_module_identifier(), {}).get("server_is_online", False),
            player_dict.get("is_online", False) and player_dict["steamid"] not in online_players
        ]):
            reset_and_update_live_status(module, player_dict)

    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid):
    for steamid, player_dict in module.dom.data.get(module.get_module_identifier(), {}).get("players", {}).items():
        if steamid == 'last_updated':
            continue

        if any([
            not module.dom.data.get(module.telnet.get_module_identifier(), {}).get("server_is_online", False),
        ]):
            reset_and_update_live_status(module, player_dict)

    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "gets a list of all currently logged in players",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
