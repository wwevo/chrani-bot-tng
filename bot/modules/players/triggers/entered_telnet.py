from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    # print("{}: {}".format(module.getName(), regex_result.re.groupindex))
    command = regex_result.group("command")
    # print(command)
    executed_trigger = False
    if command == "Authenticating":
        player_steamid = regex_result.group("player_steamid")

        player_dict = module.dom.data.get("module_players", {}).get("players", {}).get(player_steamid)
        if player_dict is None:
            player_dict = {
                "name": regex_result.group("player_name"),
                "steamid": player_steamid
            }

        player_dict["is_online"] = True
        player_dict["in_limbo"] = True
        player_dict["is_initialized"] = False

        executed_trigger = True

    if command == "connected":
        player_steamid = regex_result.group("player_steamid")

        player_dict = module.dom.data.get("module_players", {}).get("players", {}).get(player_steamid)
        if player_dict is None:
            player_dict = {
                "name": regex_result.group("player_name"),
                "steamid": player_steamid,
            }

        player_dict["id"] = regex_result.group("entity_id")
        player_dict["ip"] = regex_result.group("player_ip")
        player_dict["is_online"] = True
        player_dict["in_limbo"] = True
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
        print(player_dict)


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
