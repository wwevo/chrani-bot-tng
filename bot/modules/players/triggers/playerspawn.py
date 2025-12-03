from bot import loaded_modules_dict
from bot.constants import TELNET_PREFIXES
from bot.logger import get_logger
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]
logger = get_logger("players.playerspawn")



def main_function(bot, source_module, regex_result):
    return


trigger_meta = {
    "description": "reacts to telnets playerspawn messages for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                TELNET_PREFIXES["telnet_log"]["timestamp"] +
                r"PlayerSpawnedInWorld\s"
                r"\("
                r"reason: (?P<command>.+?),\s"
                r"position: (?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)"
                r"\):\s"
                r"EntityID=(?P<entity_id>.*),\s"
                r"PltfmId='Steam_(?P<player_steamid>.*)',\s"
                r"CrossId='(?P<cross_id>[^']+)',\s"
                r"OwnerID='(?P<owner_steamid>[^']+)',\s"
                r"PlayerName='(?P<player_name>[^']+)',\s"
                r"ClientNumber='(?P<client_number>[^']+)'"
            ),
            "callback": main_function
        }, {
            "regex": (
                TELNET_PREFIXES["telnet_log"]["timestamp"] +
                r"Player (?P<command>.*): "
                r"EntityID=(?P<entity_id>.*), "
                r"PltfmId='Steam_(?P<player_steamid>.*)', "
                r"CrossId='(?P<cross_id>[^']+)', "
                r"OwnerID='(?P<owner_id>[^']+)', "
                r"PlayerName='(?P<player_name>[^']+)'$"
            ),
            "callback": main_function
        }, {
            "regex": (
                TELNET_PREFIXES["telnet_log"]["timestamp"] +
                TELNET_PREFIXES["GMSG"]["command"]
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
