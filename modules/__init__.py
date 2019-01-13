from importlib import import_module
from os import path, chdir, walk
import json
root_dir = path.dirname(path.abspath(__file__))
chdir(root_dir)


with open('module_options.json') as open_file:
    module_options_dict = json.load(open_file)

loaded_modules_list = []
modules_list = next(walk('.'))[1]
for module in modules_list:
    import_module("modules." + module)


def load_modules():
    for loaded_module in loaded_modules_list:
        loaded_module.start(module_options_dict.get(loaded_module.get_module_identifier(), dict))
