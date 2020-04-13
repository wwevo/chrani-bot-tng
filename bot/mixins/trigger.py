from bot import loaded_modules_dict
from os import path, listdir, pardir
from importlib import import_module
import re


class Trigger(object):
    available_triggers_dict = dict

    def __init__(self):
        self.available_triggers_dict = {}

    def start(self):
        try:
            for name, triggers in self.available_triggers_dict.items():
                try:
                    for trigger, handler in triggers["handlers"].items():
                        self.dom.data.register_callback(self, trigger, handler)
                except KeyError:
                    pass
        except KeyError as error:
            pass

    def register_trigger(self, identifier, trigger_dict):
        self.available_triggers_dict[identifier] = trigger_dict

    def import_triggers(self):
        modules_root_dir = path.join(path.dirname(path.abspath(__file__)), pardir, "modules")

        module_triggers_root_dir = path.join(modules_root_dir, self.options['module_name'])
        try:
            for module_trigger in listdir(path.join(module_triggers_root_dir, "triggers")):
                if module_trigger == 'common.py' or module_trigger == '__init__.py' or module_trigger[-3:] != '.py':
                    continue
                import_module("bot.modules." + self.options['module_name'] + ".triggers." + module_trigger[:-3])

            for module_trigger in listdir(path.join(module_triggers_root_dir, "commands")):
                if module_trigger == 'common.py' or module_trigger == '__init__.py' or module_trigger[-3:] != '.py':
                    continue
                import_module("bot.modules." + self.options['module_name'] + ".commands." + module_trigger[:-3])

        except FileNotFoundError:
            pass

        except ModuleNotFoundError:
            pass

    def execute_telnet_triggers(self):
        telnet_lines_to_process = self.telnet.get_a_bunch_of_lines_from_queue(25)

        for telnet_line in telnet_lines_to_process:
            for loaded_module in loaded_modules_dict.values():
                for trigger_name, trigger_group in loaded_module.available_triggers_dict.items():
                    try:
                        for trigger in trigger_group["triggers"]:
                            regex_results = re.search(trigger["regex"], telnet_line)
                            if regex_results:
                                trigger["callback"](loaded_module, self, regex_results)
                                # TODO: add method to append log, or create a new one
                                # TODO: this needs to weed out triggers being called too often
                    except KeyError:
                        pass
