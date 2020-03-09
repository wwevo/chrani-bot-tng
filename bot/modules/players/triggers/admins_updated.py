from .discord_webhook import DiscordWebhook
from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(*args, **kwargs):
    module = args[0]

    permission_levels = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get("admins", {})
    )

    for steamid, level in permission_levels.items():
        event_data = ['update_player_permission_level', {
            'steamid': steamid,
            'level': level
        }]
        module.trigger_action_hook(module.players, event_data=event_data)


trigger_meta = {
    "description": (
        "Will call the update_player_permission_level action after permissions have been retrieved from the game"
    ),
    "main_function": main_function,
    "handlers": {
        "module_players/admins": main_function,
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
