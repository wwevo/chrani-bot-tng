from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    active_dataset = module.dom.data.get("module_environment", {}).get("active_dataset", None)
    player_steamid = regex_result.group("player_steamid")
    existing_player_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(player_steamid, None)
    )

    if command == "connected":
        # we want to mute completely new players and players that are not authenticated on login.
        if existing_player_dict is not None:
            if existing_player_dict.get("is_authenticated", False) is False:
                is_muted = True
            else:
                is_muted = False

            event_data = ['manage_player_muting', {
                'dataset': module.dom.data.get("module_environment", {}).get("active_dataset", None),
                'player_steamid': player_steamid,
                'is_muted': is_muted,
                'action': 'set mute status'
            }]
            module.trigger_action_hook(origin_module, event_data, player_steamid)


trigger_meta = {
    "description": "reacts to telnets player discovery messages for real time responses!",
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
