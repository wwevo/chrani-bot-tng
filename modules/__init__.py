from importlib import import_module
from os import path, chdir, walk
import json
root_dir = path.dirname(path.abspath(__file__))
chdir(root_dir)


loaded_modules_list = []  # this will be populated by the imports done next:
modules_to_start_dict = {}
started_modules_dict = {}

available_modules_list = next(walk('.'))[1]
for module in available_modules_list:
    """ at the bottom of each module, the loaded_modules_list will be updated
    modules may not do any stuff in their __init__, unless you know what you are doing """
    import_module("modules." + module)


def batch_setup_modules(modules_list):
    """ this should load all modules in an order they can work with
    Make absolutely SURE there's no circular dependencies, because I won't :) """
    for module_to_setup in modules_list:
        try:
            if isinstance(module_to_setup.required_modules, list):  # has dependencies, load those first!
                batch_setup_modules(module_to_setup.required_modules)
        except AttributeError:  # raised by isinstance = has no dependencies, load right away
            if module_to_setup.get_module_identifier() not in loaded_modules_list:
                try:
                    with open(path.join(root_dir, module_to_setup.get_module_identifier()) + "_options.json") as open_file:
                        module_options_dict = json.load(open_file)
                except FileNotFoundError as error:
                    module_options_dict = dict

                module_to_setup.setup(module_options_dict)
                modules_to_start_dict[module_to_setup.get_module_identifier()] = module_to_setup


def setup_modules():
    batch_setup_modules(loaded_modules_list)


def start_modules():
    for module_identifier, module_to_start in modules_to_start_dict.items():
        module_to_start.start()
        started_modules_dict[module_identifier] = module_to_start
