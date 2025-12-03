from bot import loaded_modules_dict
from bot.constants import TELNET_TIMEOUT_NORMAL, TELNET_PREFIXES
from os import path, pardir
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, action_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        module.callback_fail(callback_fail, action_meta, dispatchers_id)
        return

    regex = action_meta.get("regex")[0]
    ticket = module.telnet.send_command("listents", regex, timeout=TELNET_TIMEOUT_NORMAL)
    result = ticket.wait()

    if result['success']:
        module.callback_success(callback_success, action_meta, dispatchers_id, result['match'])
    else:
        action_meta["fail_reason"] = ["[{}] action timeout. buffer received: {}".format(action_name, result['buffer'])]
        module.callback_fail(callback_fail, action_meta, dispatchers_id)


def callback_success(module, action_meta, dispatchers_id, match=None):
    raw_entity_data = match.group("raw_entity_data").lstrip()
    if len(raw_entity_data) >= 1:
        regex = action_meta.get("regex")[1]
        entities_to_update_dict = {}

        active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
        if active_dataset is None:
            return

        for m in re.finditer(regex, raw_entity_data):
            entity_dict = {
                "id": m.group("id"),
                "owner": m.group("id"),
                "identifier": m.group("id"),
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
                "dataset": active_dataset
            }
            entities_to_update_dict[m.group("id")] = entity_dict

        if len(entities_to_update_dict) >= 1:
            module.dom.data.upsert({
                module.get_module_identifier(): {
                    active_dataset: {
                        "elements": entities_to_update_dict
                    }
                }
            })


def callback_fail(module, action_meta, dispatchers_id=None):
    return


def callback_skip(module, action_meta, dispatchers_id=None):
    return


action_meta = {
    "id": action_name,
    "description": "get all game entities",
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
            r"Executing\scommand\s\'listents\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
            r"(?P<raw_entity_data>[\s\S]*?)"
            r"Total\sof\s(?P<entity_count>\d{1,3})\sin\sthe\sgame"
        ),
        (
            r"\d{1,2}. id=(?P<id>\d+), \["
            r"type=(?P<type>.+), "
            r"name=(?P<name>.*), "
            r"id=(\d+)"
            r"\], "
            r"pos=\((?P<pos_x>.?\d+.\d), (?P<pos_y>.?\d+.\d), (?P<pos_z>.?\d+.\d)\), "
            r"rot=\((?P<rot_x>.?\d+.\d), (?P<rot_y>.?\d+.\d), (?P<rot_z>.?\d+.\d)\), "
            r"lifetime=(?P<lifetime>.+), "
            r"remote=(?P<remote>.+), "
            r"dead=(?P<dead>.+), "
            r"health=(?P<health>\d+)"
            r"\r\n"
        )
    ]
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
