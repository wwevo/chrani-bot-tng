from bot import loaded_modules_dict
from bot.constants import TELNET_PREFIXES
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(bot, source_module, regex_result):
    print(trigger_name, ": ", regex_result)
    # print(kwargs)
    return

    command = regex_result.group("command")
    executed_trigger = False

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    if command == "disconnected":
        player_steamid = regex_result.group("player_steamid")

        existing_player_dict = (
            module.dom.data
            .get("module_players", {})
            .get(active_dataset, {})
            .get("elements", {})
            .get(player_steamid, {})
        )
        player_dict = {}
        player_dict.update(existing_player_dict)
        player_dict.update({
            "is_online": False,
            "is_initialized": False
        })

        executed_trigger = True

    if executed_trigger is True:
        module.dom.data.upsert({
            "module_players": {
                active_dataset: {
                    "elements": {
                        player_steamid: player_dict
                    }
                }
            }
        })


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

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
