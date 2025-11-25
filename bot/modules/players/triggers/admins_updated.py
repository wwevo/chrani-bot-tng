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
    
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    for steamid, level in permission_levels.items():
        # Only update permission level if player exists in database
        player_exists = (
            module.dom.data
            .get("module_players", {})
            .get("elements", {})
            .get(active_dataset, {})
            .get(steamid, None)
        ) is not None
        
        if player_exists:
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
