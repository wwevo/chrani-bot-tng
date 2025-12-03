from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, callback_meta, dispatchers_id=None):
    return


trigger_meta = {
    "description": "sends player updates to webmap clients",
    "main_function": main_function,
    "handlers": {
        "module_players/%dataset%/elements/%steamid%": main_function,
    }
}

loaded_modules_dict["module_" + module_name].register_callback_handler(trigger_name, trigger_meta)
