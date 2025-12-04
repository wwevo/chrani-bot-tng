from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, callback_meta, dispatchers_id=None):
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    if not active_dataset:
        print("pass: no active dataset to work with")
        return

    original_data = callback_meta.get("original_data", {})
    updated_data = callback_meta.get("updated_data", {})

    # only dive into this when not authenticated
    if original_data.get("is_authenticated"):
        print("pass: authenticated player")
        return

    on_the_move_player_dict = (
        module.dom.data
        .get("module_players", {})
        .get(active_dataset, {})
        .get("elements", {})
        .get(updated_data.get("steamid"), {})
    )


trigger_meta = {
    "description": "reacts to every players move!",
    "main_function": main_function,
    "handlers": {
        "module_players/%dataset%/elements/%steamid%/pos": main_function,
    }
}

loaded_modules_dict["module_" + module_name].register_callback_handler(trigger_name, trigger_meta)
