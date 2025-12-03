from bot import loaded_modules_dict
from bot.constants import TELNET_PREFIXES
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, trigger_meta, dispatchers_id=None):
    return

trigger_meta = {
    "description": "reacts to telnets player disconnected message for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                TELNET_PREFIXES["telnet_log"]["timestamp"] +
                r"Player\s"
                r"(?P<command>.*):\s"
                r"EntityID=(?P<entity_id>.*),\s"
                r"PlayerID='(?P<player_steamid>\d{17})',\s"
                r"OwnerID='(?P<owner_id>\d{17})',\s"
                r"PlayerName='(?P<player_name>[^']+)'"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_telnet_trigger(trigger_name, trigger_meta)
