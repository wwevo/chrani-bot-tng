from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    # print("{}: {}".format(module.getName(), origin_module))
    player_steamid = regex_result.group("player_steamid")

    whitelist_is_active = module.dom.data.get("module_whitelist", {}).get("is_active", False)
    player_is_online = player_steamid in module.dom.data.get("module_players", {}).get("online_players", [])
    player_is_initialized = module.dom.data.get("module_players", {}).get("players", {}).get(
        player_steamid, {}
    ).get(
        "is_initialized", False
    )

    if whitelist_is_active is True and player_is_initialized is True:
        player_dict = module.dom.data.get("module_whitelist", {}).get("players", {}).get(player_steamid)
        admins = module.dom.data.get("module_players", {}).get("admins", {})
        if player_dict is not None:
            player_is_on_whitelist = player_dict.get("on_whitelist")
            if player_is_on_whitelist is True:  # or player_steamid in admins:
                # player is fine and shall be allowed to play!
                pass
            else:
                # update player_dict so this one here won't be triggered multiple times
                module.dom.data.upsert({
                    "module_players": {
                        "players": {
                            player_steamid: {
                                "is_online": False,
                                "is_initialized": False
                            }
                        }
                    }
                })
                # player is not on the whitelist # and is not an admin or mod.
                event_data = ['kickplayer', {
                    'steamid': player_steamid,
                    'reason': "you are not on our whitelist. visit"
                              "[eeffee]https://notjustfor.me/chrani-bot-tng[-] for more information"
                }]
                print("kicked player {} for not being on the whitelist".format(player_steamid))
                # print(event_data)
                module.trigger_action_hook(origin_module.players, event_data)
    else:
        return False


trigger_meta = {
    "description": "finds player steamid in the telnet-stream to take whitelist actions!",
    "main_function": main_function,
    "triggers": [
        {
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\sINF\s"
                r".*(?=[\s|\'|\"|\(|\[](?P<player_steamid>\d{17})[\s|\'|\"|\)|\]]).*"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
