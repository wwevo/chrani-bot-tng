from module import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, regex_result):
    print(regex_result.group("reason"))


trigger_meta = {
    "description": "reacts to telnets playerspawn messages for real time responses!",
    "main_function": main_function,
    "regex": [
        (
            r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
            r"PlayerSpawnedInWorld\s"
            r"\("
            r"reason: (?P<reason>.+?),\s"
            r"position: (?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)"
            r"\):\s"
            r"EntityID=(?P<entity_id>.*),\s"
            r"PlayerID='(?P<player_steamid>.*)',\s"
            r"OwnerID='(?P<owner_steamid>.*)',\s"
            r"PlayerName='(?P<player_name>.*)'"
        ), (
            r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
            r"Player (?P<reason>.*): "
            r"EntityID=(?P<entity_id>.*), "
            r"PlayerID=\'(?P<player_steamid>.*)\', "
            r"OwnerID=\'(?P<owner_id>.*)\', "
            r"PlayerName='(?P<player_name>.*)\'$"
        ), (
            r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
            r"GMSG:\sPlayer\s\'(?P<player_name>.*)\'\s(?P<reason>.*)$"
        )
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
