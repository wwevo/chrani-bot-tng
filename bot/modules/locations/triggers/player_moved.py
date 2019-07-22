from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(*args, **kwargs):
    original_values_dict = kwargs.get("original_values_dict", {})
    updated_values_dict = kwargs.get("updated_values_dict", {})
    if original_values_dict["pos"] != updated_values_dict["pos"]:
        print("moved!")
        # do stuff!
        return


trigger_meta = {
    "description": "reacts to every players move!",
    "main_function": main_function,
    "handlers": {
        "module_players/players/%steamid%/pos": main_function,
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
