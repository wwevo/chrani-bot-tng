from os import path, chdir, walk
root_dir = path.dirname(path.abspath(__file__))
chdir(root_dir)

from importlib import import_module

module_options_dict = {
    "module_webserver": {
        "Flask_secret_key": "thisissecret",
        "SocketIO_debug": True,
        "SocketIO_use_reloader": False,
        "SocketIO_asynch_mode": "gevent"
    }
}

loaded_modules_list = []
modules_list = next(walk('.'))[1]
for module in modules_list:
    import_module("modules." + module)


def load_modules():
    for loaded_module in loaded_modules_list:
        loaded_module.start(module_options_dict.get(loaded_module.get_identifier(), dict))
