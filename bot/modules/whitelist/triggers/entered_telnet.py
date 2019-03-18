from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, regex_result):
    print("{}: {}".format(module.getName(), regex_result.re.groupindex))
    command = regex_result.group("command")

    if command == "Authenticating":
        player_steamid = regex_result.group("player_steamid")

        player_dict = module.dom.data.get("module_whitelist", {}).get("players", {}).get(player_steamid)
        admins = module.dom.data.get("module_players", {}).get("admins", {})
        if player_dict is not None:
            player_is_on_whitelist = player_dict.get("on_whitelist")
            if player_is_on_whitelist is True or player_steamid in admins:
                # player is fine and shall be allowed to play!
                pass
            else:
                # player is not on the whitelist and is not an admin or mod.
                whitelist_is_active = module.dom.data.get("module_whitelist", {}).get("is_active", False)
                if whitelist_is_active is True:
                    # if whitelist is active, get rid of the player!
                    pass


trigger_meta = {
    "description": "finds player steamid in the login-stream to take whitelist actions!",
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
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
