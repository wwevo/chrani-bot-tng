from .discord_webhook import DiscordWebhook
from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_steamid = regex_result.group("player_steamid")
    existing_player_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(active_dataset, {})
        .get(player_steamid, None)
    )

    executed_trigger = False
    player_dict = {}
    if command in ["Authenticating", "connected"]:
        if existing_player_dict is None:
            player_dict = {
                "name": regex_result.group("player_name"),
                "steamid": player_steamid,
                "pos": {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                },
                "dataset": active_dataset,
                "owner": player_steamid,
                "last_seen_gametime": module.game_environment.get_last_recorded_gametime()
            }
        else:
            player_dict.update(existing_player_dict)

        player_dict.update({
            "is_online": True,
            "in_limbo": True,
            "is_initialized": False,
        })

        if command == "connected":
            player_dict.update({
                "id": regex_result.group("entity_id"),
                "ip": regex_result.group("player_ip")
            })

        player_name = player_dict.get("name", regex_result.group("player_name"))
        servertime_player_joined = (
            module.dom.data
            .get("module_game_environment", {})
            .get(active_dataset, {})
            .get("last_recorded_gametime", {})
        )
        last_seen_gametime_string = "Day {day}, {hour}:{minute}".format(
            day=servertime_player_joined.get("day", "00"),
            hour=servertime_player_joined.get("hour", "00"),
            minute=servertime_player_joined.get("minute", "00")
        )
        payload = '{} is logging into the a18 test-server at {}'.format(player_name, last_seen_gametime_string)

        discord_payload_url = origin_module.options.get("discord_webhook", None)
        if discord_payload_url is not None:
            webhook = DiscordWebhook(
                url=discord_payload_url,
                content=payload
            )
            webhook.execute()
        executed_trigger = True

    if all([
        executed_trigger is True,
        active_dataset is not None,
        player_steamid is not None,
        len(player_dict) >= 1
    ]):
        module.dom.data.upsert({
            "module_players": {
                "elements": {
                    active_dataset: {
                        player_steamid: player_dict
                    }
                }
            }
        })

trigger_meta = {
    "description": "reacts to telnets player discovery messages for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                r"\[Steamworks.NET\]\s"
                r"(?P<command>.*)\s"
                r"player:\s(?P<player_name>.*)\s"
                r"SteamId:\s(?P<player_steamid>\d+)\s(.*)"
            ),
            "callback": main_function
        }, {
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
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

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
