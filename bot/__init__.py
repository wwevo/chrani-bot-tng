""" some IDE's will throw 'PEP 8' warnings for imports, but this has to happen early, I think """
from gevent import monkey
monkey.patch_all()

""" standard imports """
from importlib import import_module
from os import path, chdir, walk
import json
from collections import deque
root_dir = path.dirname(path.abspath(__file__))
chdir(root_dir)

loaded_modules_dict = {}  # this will be populated by the imports done next:
modules_to_start_list = deque()
module_loading_order = []
started_modules_dict = {}

available_modules_list = next(walk(path.join('modules', '.')))[1]

for module in available_modules_list:
    """ at the bottom of each module, the loaded_modules_list will be updated
    modules may not do any stuff in their __init__, apart from setting variables
    and calling static methods, unless you know what you are doing """
    import_module("bot.modules." + module)


def batch_setup_modules(modules_list):
    if len(module_loading_order) >= 1:
        for module_to_setup in module_loading_order:
            try:
                options_dir = "{}/{}".format(root_dir, "options")
                with open(path.join(options_dir, module_to_setup + ".json")) as open_file:
                    module_options_dict = json.load(open_file)
            except FileNotFoundError as error:
                module_options_dict = dict

            loaded_modules_dict[module_to_setup].setup(module_options_dict)
            modules_to_start_list.append(loaded_modules_dict[module_to_setup])

    else:
        """ this should load all module in an order they can work with
        Make absolutely SURE there's no circular dependencies, because I won't :) """
        for module_to_setup in modules_list:
            try:
                if isinstance(loaded_modules_dict[module_to_setup].required_modules, list):  # has dependencies, load those first!
                    batch_setup_modules(loaded_modules_dict[module_to_setup].required_modules)
                    raise AttributeError
            except AttributeError:  # raised by isinstance = has no dependencies, load right away
                if loaded_modules_dict[module_to_setup] not in modules_to_start_list:
                    try:
                        options_dir = "{}/{}".format(root_dir, "options")
                        with open(path.join(options_dir, module_to_setup + ".json")) as open_file:
                            module_options_dict = json.load(open_file)
                    except FileNotFoundError as error:
                        module_options_dict = dict

                    loaded_modules_dict[module_to_setup].setup(module_options_dict)
                    modules_to_start_list.append(loaded_modules_dict[module_to_setup])


def setup_modules():
    loaded_modules_identifier_list = []
    for loaded_module_identifier, loaded_module in loaded_modules_dict.items():
        loaded_modules_identifier_list.append(loaded_module.get_module_identifier())

    batch_setup_modules(loaded_modules_identifier_list)


def start_modules():
    for module_to_start in modules_to_start_list:
        module_to_start.start()
        started_modules_dict[module_to_start.get_module_identifier()] = module_to_start
    if len(loaded_modules_dict) == len(started_modules_dict):
        print("all modules started")
