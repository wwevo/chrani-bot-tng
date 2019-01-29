from module import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
trigger_name = path.basename(path.abspath(__file__))[:-3]


print("imported trigger {}!".format(trigger_name))


trigger_meta = {
    "description": "reacts to telnets login messages for real time responses!",
}

loaded_modules_dict["module_" + module_name].register_trigger(trigger_name, trigger_meta)
