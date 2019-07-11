from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, dispatchers_steamid=None):
    pass


def update_widget(module, updated_values_dict=None, old_values_dict=None, original_values_dict=None, dispatchers_steamid=None):
    admin_dict = updated_values_dict.get("admins", {})
    # print("found admins:{}".format(admin_dict))


widget_meta = {
    "description": "for now, this just prints the admin list when changed ^^",
    "main_widget": main_widget,
    "handlers": {
        "module_players/admins": update_widget
    },
    "enabled": False
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
