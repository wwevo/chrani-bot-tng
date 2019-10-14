from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    # print("{}: {}".format(module.getName(), regex_result.re.groupindex))
    command = regex_result.group("command")
    executed_trigger = False
    current_map_identifier = module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName", None)

    if command == "disconnected":
        player_steamid = regex_result.group("player_steamid")

        player_dict = module.dom.data.get("module_players", {}).get("elements", {}).get(current_map_identifier, {}).get(player_steamid, {})
        player_dict["is_online"] = False
        player_dict["is_initialized"] = False

        executed_trigger = True

    if executed_trigger is True:
        module.dom.data.upsert({
            "module_players": {
                "players": {
                    player_steamid: player_dict
                }
            }
        })


trigger_meta = {
    "description": "reacts to telnets player disconnected message for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Player (?P<command>.*): "
                r"EntityID=(?P<entity_id>[-1]\d+), "
                r"PlayerID='(?P<player_steamid>\d{17})', "
                r"OwnerID='(?P<owner_id>\d{17})', "
                r"PlayerName='(?P<player_name>.*)'"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
