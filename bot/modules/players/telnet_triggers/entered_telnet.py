from bot import loaded_modules_dict
from bot.constants import TELNET_PREFIXES
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, trigger_meta, dispatchers_id=None):
    print(trigger_name, ": ", trigger_meta["regex_result"])
    # print(kwargs)
    return

    command = trigger_meta["regex_result"].group("command")
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    player_steamid = trigger_meta["regex_result"].group("player_steamid")
    existing_player_dict = (
        module.dom.data
        .get("module_players", {})
        .get(active_dataset, {})
        .get("elements", {})
        .get(player_steamid, None)
    )

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if active_dataset is None:
        return None

    last_seen_gametime = (
        module.dom.data
        .get("module_game_environment", {})
        .get(active_dataset, {})
        .get("last_recorded_gametime", {})
    )

    executed_trigger = False
    player_dict = {}
    if command in ["Authenticating", "connected"]:
        if existing_player_dict is None:
            player_dict = {
                "name": trigger_meta["regex_result"].group("player_name"),
                "steamid": player_steamid,
                "pos": {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                },
                "dataset": active_dataset,
                "owner": player_steamid,
                "last_seen_gametime": last_seen_gametime
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
                "id": trigger_meta["regex_result"].group("entity_id"),
                "ip": trigger_meta["regex_result"].group("player_ip"),
                "steamid": player_steamid,
                "owner": player_steamid
            })

        executed_trigger = True

    if all([
        executed_trigger is True,
        active_dataset is not None,
        player_steamid is not None,
        len(player_dict) >= 1
    ]):
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
