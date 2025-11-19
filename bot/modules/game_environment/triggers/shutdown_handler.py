from bot import loaded_modules_dict
from bot import telnet_prefixes
from bot.logger import get_logger
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]
logger = get_logger("game_environment.shutdown_handler")


def main_function(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", {})

    cancel_shutdown = updated_values_dict.get("cancel_shutdown", None)
    force_shutdown = updated_values_dict.get("force_shutdown", None)

    if cancel_shutdown:
        logger.info("shutdown_cancelled")
    if force_shutdown:
        logger.info("shutdown_forced")


trigger_meta = {
    "description": "reacts to changes in the shutdown procedure",
    "main_function": main_function,
    "handlers": {
        "module_game_environment/%map_identifier%/cancel_shutdown": main_function,
        "module_game_environment/%map_identifier%/force_shutdown": main_function
    }
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
