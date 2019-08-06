from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    # print("{}: {}".format(module.getName(), regex_result.re.groupindex))
    command = regex_result.group("command")
    player_name = regex_result.group("player_name")
    entity_id = regex_result.group("entity_id")
    print(player_name, ":", entity_id, ":", command)


trigger_meta = {
    "description": "catches location commands from the players chat and then adds them to the database",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"\(BCM\)\sGlobal\:(?P<player_name>.*)\:(?P<entity_id>.*)\:\s(?P<command>.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
