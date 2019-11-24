from .discord_webhook import DiscordWebhook
from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)
    # print("{module}: {available_vars}, {command}".format(
    #     module=module.getName(),
    #     available_vars=regex_result.re.groupindex,
    #     command=command
    # ))

    if command == "joined the game":
        player_name = regex_result.group("player_name")
        servertime_player_joined = (
            module.dom.data
            .get("module_environment", {})
            .get(current_map_identifier, {})
            .get("last_recorded_gametime", {})
        )
        last_seen_gametime_string = "Day {day}, {hour}:{minute}".format(
            day=servertime_player_joined.get("day", "00"),
            hour=servertime_player_joined.get("hour", "00"),
            minute=servertime_player_joined.get("minute", "00")
        )
        payload = '{} joined the a18 test-server at {}'.format(player_name, last_seen_gametime_string)

        discord_payload_url = origin_module.options.get("discord_webhook", None)
        webhook = DiscordWebhook(
            url=discord_payload_url,
            content=payload
        )
        webhook.execute()

    if command == "JoinMultiplayer":
        steamid = regex_result.group("player_steamid")
        player_name = regex_result.group("player_name")
        current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)
        player_dict = (
            module.dom.data.get("module_players", {})
            .get("elements", {})
            .get(current_map_identifier, {})
            .get(steamid, {})
        )

        if player_dict.get("is_authenticated", False) is True:
            message = "[66FF66]Welcome back[-] [FFFFFF]{}[-]".format(player_name)
        else:
            message = (
                "[66FF66]Welcome to the server[-] [FFFFFF]{player_name}[-], "
                "[FF6666]please authenticate[-] [FFFFFF]and make yourself at home :)[-]"
            ).format(
                player_name=player_name
            )
        event_data = ['say_to_player', {
            'steamid': steamid,
            'message': message
        }]
        module.trigger_action_hook(origin_module.players, event_data, steamid)


trigger_meta = {
    "description": "reacts to telnets playerspawn messages for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"PlayerSpawnedInWorld\s"
                r"\("
                r"reason: (?P<command>.+?),\s"
                r"position: (?P<pos_x>.*),\s(?P<pos_y>.*),\s(?P<pos_z>.*)"
                r"\):\s"
                r"EntityID=(?P<entity_id>.*),\s"
                r"PlayerID='(?P<player_steamid>.*)',\s"
                r"OwnerID='(?P<owner_steamid>.*)',\s"
                r"PlayerName='(?P<player_name>.*)'"
            ),
            "callback": main_function
        }, {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"Player (?P<command>.*): "
                r"EntityID=(?P<entity_id>.*), "
                r"PlayerID=\'(?P<player_steamid>.*)\', "
                r"OwnerID=\'(?P<owner_id>.*)\', "
                r"PlayerName='(?P<player_name>.*)\'$"
            ),
            "callback": main_function
        }, {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r"GMSG:\sPlayer\s\'(?P<player_name>.*)\'\s(?P<command>.*)$"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
