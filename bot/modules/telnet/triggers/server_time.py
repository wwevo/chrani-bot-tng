from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, regex_result):
    # print("{}: {}".format(module.getName(), regex_result.re.groupindex))
    datetime = regex_result.group("datetime")
    executed_trigger = False
    if datetime is not None:
        executed_trigger = True

    if executed_trigger is True:
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
            "regex": (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+).*"
            ),
            "callback": main_function
        }
    ]
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
