from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(*args, **kwargs):
    module = args[0]
    original_values_dict = kwargs.get("original_values_dict", {})
    updated_values_dict = kwargs.get("updated_values_dict", {})
    player_steamid = original_values_dict.get("owner", None)
    is_authenticated = updated_values_dict.get("is_authenticated", None)

    try:
        if all([
            len(original_values_dict) >= 1,
            is_authenticated is not None,
            player_steamid is not None
        ]):
            event_data = ['manage_player_muting', {
                'dataset': module.dom.data.get("module_game_environment", {}).get("active_dataset", None),
                'player_steamid': player_steamid,
                'action': 'set mute status'
            }]

            if is_authenticated:
                event_data[1]["is_muted"] = False
            else:
                event_data[1]["is_muted"] = True

            module.trigger_action_hook(module, event_data=event_data)
    except AttributeError:
        pass


trigger_meta = {
    "description": "reacts to a players authentication change",
    "main_function": main_function,
    "handlers": {
        "module_players/elements/%map_identifier%/%steamid%/is_authenticated": main_function,
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
