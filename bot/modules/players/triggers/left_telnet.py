from .discord_webhook import DiscordWebhook
from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    command = regex_result.group("command")
    executed_trigger = False

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    if command == "disconnected":
        player_steamid = regex_result.group("player_steamid")

        existing_player_dict = (
            module.dom.data
            .get("module_players", {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(player_steamid, {})
        )
        player_dict = {}
        player_dict.update(existing_player_dict)
        player_dict.update({
            "is_online": False,
            "is_initialized": False
        })

        player_name = player_dict.get("name", regex_result.group("player_name"))
        servertime_player_left = (
            module.dom.data
            .get("module_game_environment", {})
            .get(active_dataset, {})
            .get("last_recorded_gametime", {})
        )
        last_seen_gametime_string = "Day {day}, {hour}:{minute}".format(
            day=servertime_player_left.get("day", "00"),
            hour=servertime_player_left.get("hour", "00"),
            minute=servertime_player_left.get("minute", "00")
        )
        payload = '{} left {} at {}'.format(player_name, active_dataset, last_seen_gametime_string)

        discord_payload_url = origin_module.options.get("discord_webhook", None)
        if discord_payload_url is not None:
            webhook = DiscordWebhook(
                url=discord_payload_url,
                content=payload
            )
            webhook.execute()

        executed_trigger = True

    if executed_trigger is True:
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
    "description": "reacts to telnets player disconnected message for real time responses!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                telnet_prefixes["telnet_log"]["timestamp"] +
                r"Player\s"
                r"(?P<command>.*):\s"
                r"EntityID=(?P<entity_id>.*),\s"
                r"PlayerID='(?P<player_steamid>\d{17})',\s"
                r"OwnerID='(?P<owner_id>\d{17})',\s"
                r"PlayerName='(?P<player_name>.*)'"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
