from importlib import import_module
from os import path, listdir, pardir
import re


class TelnetTrigger(object):
    """
    Handles regex-based triggers for Telnet input.

    Monitors Telnet lines and executes callbacks when regex patterns match.
    All handlers follow the signature: handler(module, trigger_meta, dispatchers_id=None)

    trigger_meta contains:
    - regex_result: the regex match object
    - source_module: the module that received the Telnet line
    - telnet_line: the original line (optional)
    """
    available_telnet_triggers_dict = dict
    unmatched_patterns_dict = dict

    def __init__(self):
        self.available_telnet_triggers_dict = {}
        self.unmatched_patterns_dict = {}

    def register_telnet_trigger(self, identifier, trigger_dict):
        """Register a telnet trigger with this module"""
        self.available_telnet_triggers_dict[identifier] = trigger_dict

    def import_telnet_triggers(self):
        """
        Import telnet triggers from module directories.
        Looks in telnet_triggers/ directory (includes former commands).
        """
        modules_root_dir = path.join(path.dirname(path.abspath(__file__)), pardir, "modules")
        module_root_dir = path.join(modules_root_dir, self.options['module_name'])

        # Import from telnet_triggers directory (includes both triggers and commands)
        try:
            telnet_triggers_dir = path.join(module_root_dir, "telnet_triggers")
            for trigger_file in listdir(telnet_triggers_dir):
                if trigger_file in ('common.py', '__init__.py') or not trigger_file.endswith('.py'):
                    continue
                import_module("bot.modules." + self.options['module_name'] + ".telnet_triggers." + trigger_file[:-3])
        except (FileNotFoundError, ModuleNotFoundError):
            pass

    def execute_telnet_triggers(self):
        """
        Process Telnet lines and execute matching triggers.
        Called by Telnet module during its run loop.
        """
        from bot import loaded_modules_dict

        telnet_lines_to_process = self.telnet.get_a_bunch_of_lines_from_queue(25)

        for telnet_line in telnet_lines_to_process:
            line_matched = False

            # Check all modules for matching triggers
            for loaded_module in loaded_modules_dict.values():
                for trigger_name, trigger_group in loaded_module.available_telnet_triggers_dict.items():
                    try:
                        for trigger in trigger_group["triggers"]:
                            regex_result = re.search(trigger["regex"], telnet_line)
                            if regex_result:
                                # Build trigger_meta
                                trigger_meta = {
                                    "regex_result": regex_result,
                                    "source_module": self,
                                    "telnet_line": telnet_line
                                }

                                # Call with unified signature
                                trigger["callback"](loaded_module, trigger_meta, dispatchers_id=None)
                                line_matched = True
                    except KeyError:
                        # Trigger group doesn't have "triggers" key (might be callback-based)
                        pass

    @staticmethod
    def get_all_available_telnet_triggers_dict():
        """Get all registered telnet triggers from all loaded modules"""
        from bot import loaded_modules_dict
        all_triggers = {}
        for module_id, module in loaded_modules_dict.items():
            if hasattr(module, 'available_telnet_triggers_dict') and len(module.available_telnet_triggers_dict) >= 1:
                all_triggers[module_id] = module.available_telnet_triggers_dict
        return all_triggers
