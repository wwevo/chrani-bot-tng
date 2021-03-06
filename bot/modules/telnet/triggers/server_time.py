from bot import loaded_modules_dict
from bot import telnet_prefixes
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(origin_module, module, regex_result):
    datetime = regex_result.group("datetime")
    last_recorded_datetime = module.dom.data.get("module_telnet", {}).get("last_recorded_servertime", "")
    executed_trigger = False
    if datetime is not None:
        executed_trigger = True

    if all([
        executed_trigger is True,
        datetime > last_recorded_datetime
    ]):
        module.dom.data.upsert({
            "module_telnet": {
                "last_recorded_servertime": datetime
            }
        })


trigger_meta = {
    "description": "will update the servertime whenever a telnet line contains it",
    "main_function": main_function,
    "triggers": [
        {
            "regex": telnet_prefixes["telnet_log"]["timestamp"],
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
