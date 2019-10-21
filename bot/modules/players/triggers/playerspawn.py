from .discord_webhook import DiscordWebhook
from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    # print("{}: {}".format(module.getName(), regex_result.re.groupindex))
    command = regex_result.group("command")

    if command == "joined the game":
        # print(command, regex_result.re.groupindex)
        player_name = regex_result.group("player_name")
        payload = '{} joined the a18 test-server'.format(player_name)

        discord_payload_url = origin_module.options.get("discord_webhook", None)
        webhook = DiscordWebhook(
            url=discord_payload_url,
            content=payload
        )
        webhook.execute()


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
