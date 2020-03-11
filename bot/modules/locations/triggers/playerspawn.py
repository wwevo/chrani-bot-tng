from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    player_dict = {
        "pos": {
            "x":  regex_result.group("pos_x"),
            "y": regex_result.group("pos_y"),
            "z": regex_result.group("pos_z")
        }
    }
    player_steamid = regex_result.group("player_steamid")

    servertime_player_joined = (
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("last_recorded_gametime", {})
    )
    first_seen_gametime_string = "Day {day}, {hour}:{minute}".format(
        day=servertime_player_joined.get("day", "00"),
        hour=servertime_player_joined.get("hour", "00"),
        minute=servertime_player_joined.get("minute", "00")
    )

    event_data = ['edit_location', {
        'location_coordinates': {
            "x": player_dict["pos"]["x"],
            "y": player_dict["pos"]["y"],
            "z": player_dict["pos"]["z"]
        },
        'location_name': "Initial Spawn",
        'action': 'create_new',
        'location_enabled': True,
        'last_changed': first_seen_gametime_string
    }]
    module.trigger_action_hook(origin_module, event_data=event_data)


trigger_meta = {
    "description": "reacts to any initial playerspawn",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"PlayerSpawnedInWorld\s"
                r"\("
                r"reason: EnterMultiplayer,\s"
                r"position: (?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)"
                r"\):\s"
                r"EntityID=(?P<entity_id>.*),\s"
                r"PlayerID='(?P<player_steamid>.*)',\s"
                r"OwnerID='(?P<owner_steamid>.*)',\s"
                r"PlayerName='(?P<player_name>.*)'"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
