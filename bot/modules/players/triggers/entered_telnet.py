from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, regex_result):
    print("{}: {}".format(module.getName(), regex_result.re.groupindex))


trigger_meta = {
    "description": "reacts to telnets player dicovery messages for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"\[Steamworks.NET\]\s"
                r"(?P<command>.*)\s"
                r"player:\s(?P<player_name>.*)\s"
                r"SteamId:\s(?P<player_steamid>\d+)\s(.*)"
            ),
            "callback": main_function
        }, {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Player (?P<command>.*), "
                r"entityid=(?P<entity_id>.*), "
                r"name=(?P<player_name>.*), "
                r"steamid=(?P<player_steamid>.*), "
                r"steamOwner=(?P<owner_id>.*), "
                r"ip=(?P<player_ip>.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
