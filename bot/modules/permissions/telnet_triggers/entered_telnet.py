from bot import loaded_modules_dict
from bot.constants import TELNET_PREFIXES
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, trigger_meta, dispatchers_id=None):
    regex_result = trigger_meta["regex_result"]
    source_module = trigger_meta["source_module"]

    print(trigger_name, ": ", regex_result)
    return

    command = regex_result.group("command")
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_steamid = regex_result.group("player_steamid")
    existing_player_dict = (
        module.dom.data
        .get("module_players", {})
        .get(active_dataset, {})
        .get("elements", {})
        .get(player_steamid, None)
    )

    if command == "connected":
        # we want to mute completely new players and players that are not authenticated on login.
        if existing_player_dict is not None:
            default_player_password = module.default_options.get("default_player_password", None)
            player_is_authenticated = existing_player_dict.get("is_authenticated", False)
            if not player_is_authenticated and default_player_password is not None:
                is_muted = True
            else:
                is_muted = False

            event_data = ['set_player_mute', {
                'dataset': module.dom.data.get("module_game_environment", {}).get("active_dataset", None),
                'player_steamid': player_steamid,
                'is_muted': is_muted
            }]
            module.trigger_action_hook(origin_module, event_data=event_data)


trigger_meta = {
    "description": "reacts to telnets player discovery messages for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                TELNET_PREFIXES["telnet_log"]["timestamp"] +
                r"\[Steamworks.NET\]\s"
                r"(?P<command>.*)\s"
                r"player:\s(?P<player_name>.*)\s"
                r"SteamId:\s(?P<player_steamid>\d+)\s(.*)"
            ),
            "callback": main_function
        }, {
            "regex": (
                TELNET_PREFIXES["telnet_log"]["timestamp"] +
                r"Player\s"
                r"(?P<command>.*), "
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

loaded_modules_dict["module_" + module_name].register_telnet_trigger(trigger_name, trigger_meta)
