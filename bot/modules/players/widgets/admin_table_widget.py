from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def update_widget(module, updated_values_dict, old_values_dict):
    admin_dict = updated_values_dict.get("admins", {})
    print(admin_dict)


widget_meta = {
    "description": "for now, this just prints the admin list when changed ^^",
    "main_widget": None,
    "handlers": {
        "module_players/admins": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
