from os import path, listdir
from importlib import import_module


class Action(object):
    available_actions_dict = dict

    def __init__(self):
        self.available_actions_dict = {}

    def register_action(self, identifier, action_dict):
        self.available_actions_dict[identifier] = action_dict

    def import_actions(self):
        modules_root_dir = path.dirname(path.abspath(__file__))

        module_actions_root_dir = path.join(modules_root_dir, self.options['module_name'], "actions")
        try:
            for module_action in listdir(module_actions_root_dir):
                if module_action == 'common.py' or module_action == '__init__.py' or module_action[-3:] != '.py':
                    continue
                import_module("module." + self.options['module_name'] + ".actions." + module_action[:-3])
        except FileNotFoundError as error:
            # module does not have actions
            pass
