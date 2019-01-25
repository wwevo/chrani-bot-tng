from modules import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 3  # [seconds]
    timeout_start = time()

    module.telnet.add_telnet_command_to_queue("lp")
    poll_is_finished = False
    regex = (
        r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
        r"Executing command \'lp\' by Telnet from (.*)([\s\S]+?)Total of (\d{1,2}) in the game"
    )
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer):
            poll_is_finished = True

        if match:
            callback_success(module, event_data, dispatchers_steamid, match)
            return

    callback_fail(module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match):
    online_players_raw = match.group(4).lstrip()
    for m in re.finditer(r"\d{1,2}. id=(\d+), (.+), pos=\((.?\d+.\d), (.?\d+.\d), (.?\d+.\d)\), rot=\((.?\d+.\d), (.?\d+.\d), (.?\d+.\d)\), remote=(\w+), health=(\d+), deaths=(\d+), zombies=(\d+), players=(\d+), score=(\d+), level=(\d+), steamid=(\d+), ip=(.*), ping=(\d+)\r\n", online_players_raw):
        module.dom.upsert({
            module.get_module_identifier(): {
                m.group(16): {
                    "entityid": m.group(1),
                    "name": str(m.group(2)),
                    "position": {
                        "pos_x": float(m.group(3)),
                        "pos_y": float(m.group(4)),
                        "pos_z": float(m.group(5)),
                        "rot_x": float(m.group(6)),
                        "rot_y": float(m.group(7)),
                        "rot_z": float(m.group(8)),
                        "stardate": match.group("stardate")
                    },
                    "remote": bool(m.group(9)),
                    "health": int(m.group(10)),
                    "deaths": int(m.group(11)),
                    "zombies": int(m.group(12)),
                    "players": int(m.group(13)),
                    "score": m.group(14),
                    "level": m.group(15),
                    "steamid": m.group(16),
                    "ip": str(m.group(17)),
                    "ping": int(m.group(18)),
                }
            }
        })

    module.update_player_table_widget_frontend()
    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid):
    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "gets a list of all currently logged in players",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
