from os import path, listdir
from importlib import import_module


class Trigger(object):

    def __init__(self):
        pass

    def register_trigger(self, identifier, trigger_dict):
        self.available_triggers_dict[identifier] = trigger_dict

    def import_triggers(self):
        modules_root_dir = path.dirname(path.abspath(__file__))

        module_triggers_root_dir = path.join(modules_root_dir, self.options['module_name'], "triggers")
        try:
            for module_trigger in listdir(module_triggers_root_dir):
                if module_trigger == 'common.py' or module_trigger == '__init__.py' or module_trigger[-3:] != '.py':
                    continue
                import_module("module." + self.options['module_name'] + ".triggers." + module_trigger[:-3])
        except FileNotFoundError as error:
            # module does not have triggers
            pass
