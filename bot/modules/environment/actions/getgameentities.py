from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    timeout = 3  # [seconds]
    timeout_start = time()

    module.telnet.add_telnet_command_to_queue("listents")
    poll_is_finished = False
    regex = (
        r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
        r"INF Executing\scommand\s\'listents\'\sby\sTelnet\sfrom\s(?P<called_by>.*)"
        r"(?P<raw_entity_data>[\s\S]+?)"
        r"Total\sof\s(?P<playercount>\d{1,2})\sin\sthe\sgame"
    )

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
    raw_entity_data = match.group("raw_entity_data").lstrip()
    if len(raw_entity_data) >= 1:
        regex = (
            r"\d{1,2}. id=(?P<id>\d+), \["
            r"type=(?P<type>.+), "
            r"name=(?P<name>.+).*"
            r"\], "
            r"pos=\((?P<pos_x>.?\d+.\d), (?P<pos_y>.?\d+.\d), (?P<pos_z>.?\d+.\d)\), "
            r"rot=\((?P<rot_x>.?\d+.\d), (?P<rot_y>.?\d+.\d), (?P<rot_z>.?\d+.\d)\), "
            r"lifetime=(?P<lifetime>.+), "
            r"remote=(?P<remote>.+), "
            r"dead=(?P<dead>.+), "
            r"health=(?P<health>\d+)"
            r"\r\n"
        )
        entities_to_update_dict = {}

        current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)
        if current_map_identifier is None:
            return

        for m in re.finditer(regex, raw_entity_data):
            entity_dict = {
                "id": m.group("id"),
                "type": str(m.group("type")),
                "name": str(m.group("name")),
                "pos": {
                    "x": int(float(m.group("pos_x"))),
                    "y": int(float(m.group("pos_y"))),
                    "z": int(float(m.group("pos_z"))),
                },
                "rot": {
                    "x": int(float(m.group("rot_x"))),
                    "y": int(float(m.group("rot_y"))),
                    "z": int(float(m.group("rot_z"))),
                },
                "lifetime": str(m.group("lifetime")),
                "remote": bool(m.group("remote")),
                "dead": bool(m.group("dead")),
                "health": int(m.group("health")),
                "origin": current_map_identifier
            }
            entities_to_update_dict[m.group("id")] = entity_dict

        if len(entities_to_update_dict) >= 1:
            print(entities_to_update_dict)


def callback_fail(module, event_data, dispatchers_steamid):
    pass


def skip_it(module, event_data, dispatchers_steamid=None):
    pass


action_meta = {
    "description": "get game entities",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "skip_it": skip_it,
    "requires_telnet_connection": True,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
