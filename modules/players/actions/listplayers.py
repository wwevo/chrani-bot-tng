from modules import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def reset_and_update_live_status(module, target_steamid, conditions):
    if any(conditions):
        online_players_list = module.dom.data.get("module_environment", {}).get("online_players_list", [])
        online_players_list.append(target_steamid)
        module.dom.upsert({
            module.get_module_identifier(): {
                "online_players_list": online_players_list
            }
        }, telnet_datetime=time())
        module.dom.data[module.get_module_identifier()]["players"][target_steamid]["is_online"] = False
        module.dom.data[module.get_module_identifier()]["players"][target_steamid]["in_limbo"] = False
        module.update_player_table_widget_table_row(target_steamid)


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
    online_players_list = module.dom.data.get("module_environment", {}).get("online_players_list", [])
    for m in re.finditer(regex, raw_playerdata):
        in_limbo = True if int(m.group("health")) == 0 else False
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
        }
        module.dom.upsert({
            module.get_module_identifier(): {
                "players": {
                    m.group("steamid"): player_dict
                }
            }
        }, telnet_datetime=telnet_datetime)
        if m.group("steamid") not in online_players_list:
            module.update_player_table_widget_table_row(m.group("steamid"))
            online_players_list.append(m.group("steamid"))
            module.dom.upsert({
                "module_environment": {
                    "online_players_list": online_players_list
                }
            }, telnet_datetime=telnet_datetime)
        else:
            module.update_player_table_widget_data(m.group("steamid"))


    for steamid, player_dict in module.dom.data.get(module.get_module_identifier(), {}).get("players", {}).items():
        if steamid == 'last_updated':
            continue

        reset_and_update_live_status(
            module,
            steamid, [
                not module.dom.data.get(module.telnet.get_module_identifier(), {}).get("server_is_online", False),
                player_dict.get("is_online", False) and steamid not in online_players_list
            ])

    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid):
    for steamid, player_dict in module.dom.data.get(module.get_module_identifier(), {}).get("players", {}).items():
        if steamid == 'last_updated':
            continue

        reset_and_update_live_status(
            module,
            steamid, [
                not module.dom.data.get(module.telnet.get_module_identifier(), {}).get("server_is_online", False),
            ])

    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "gets a list of all currently logged in players",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
