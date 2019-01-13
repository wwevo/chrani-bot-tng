from importlib import import_module
from os import path, chdir, walk
import json
root_dir = path.dirname(path.abspath(__file__))
chdir(root_dir)


with open('module_options.json') as open_file:
    module_options_dict = json.load(open_file)

loaded_modules_list = []  # this will be populated by the imports done next:
available_modules_list = next(walk('.'))[1]
for module in available_modules_list:
    """ at the bottom of each module, the loaded_modules_list will be updated
    modules may not do any stuff in their __init__, unless you know what you are doing """
    import_module("modules." + module)

started_modules_list = []
def batch_start_modules(modules_list):
    """ this should load all modules in an order they can work with
    Make absolutely SURE there's no circular dependencies, because I won't :)"""
    for module in modules_list:
        try:
            if isinstance(module.required_modules, list):  # has dependencies, load those first!
                batch_start_modules(module.required_modules)
        except AttributeError:  # has no dependencies, load right away
            if module.get_module_identifier() not in loaded_modules_list:
                module.start(module_options_dict.get(module.get_module_identifier(), dict))
                started_modules_list.append(module.get_module_identifier())


def start_modules():
    batch_start_modules(loaded_modules_list)
