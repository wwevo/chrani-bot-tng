from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    player_name = regex_result.group("player_name")
    command = regex_result.group("command")

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    all_players_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(active_dataset)
    )

    steamid = None
    servertime_player_died = "n/A"
    for player_steamid, player_dict in all_players_dict.items():
        if player_dict["name"] == player_name:
            steamid = player_steamid
            servertime_player_died = player_dict.get("last_seen_gametime", servertime_player_died)
            break

    if steamid is None:
        return

    if command == 'died':
        event_data = ['edit_location', {
            'location_coordinates': {
                "x": player_dict["pos"]["x"],
                "y": player_dict["pos"]["y"],
                "z": player_dict["pos"]["z"]
            },
            'location_name': "Place of Death",
            'action': 'edit',
            'location_enabled': True,
            'last_changed': servertime_player_died
        }]
        module.trigger_action_hook(origin_module, event_data=event_data, dispatchers_steamid=steamid)


trigger_meta = {
    "description": "reacts to telnets player dying message",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\sGMSG:\s"
                r"Player\s\'(?P<player_name>.*)\'\s(?P<command>.*)"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
