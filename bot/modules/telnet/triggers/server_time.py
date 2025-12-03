from bot import loaded_modules_dict
from bot.constants import TELNET_PREFIXES
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(bot, **kwargs):
    datetime = kwargs.get("regex_results").group("datetime")

    if datetime:
        bot.dom.data.upsert({
            "module_telnet": {
                "last_recorded_servertime": datetime
            }
        })


trigger_meta = {
    "description": "updates last_recorded_servertime",
    "main_function": main_function,
    "triggers": [{
        "regex": TELNET_PREFIXES["telnet_log"]["timestamp"],
        "callback": main_function
    }]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
