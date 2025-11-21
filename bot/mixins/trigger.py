from bot import loaded_modules_dict
from os import path, listdir, pardir
from importlib import import_module
from time import time
import re
import hashlib


class Trigger(object):
    available_triggers_dict = dict
    unmatched_patterns_dict = dict

    def __init__(self):
        self.available_triggers_dict = {}
        self.unmatched_patterns_dict = {}

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

    def _extract_line_pattern(self, telnet_line: str) -> str:
        """
        Extract normalized pattern from telnet line by replacing variable parts.

        Example:
            Input:  "2025-11-21T11:42:33 232945.436 INF ... VehicleManager write #10, id 167772, ..."
            Output: "VehicleManager write #<NUM>, id <NUM>, <VEHICLE_TYPE>, (<COORD>), chunk <CHUNK>"
        """
        pattern = telnet_line

        # Replace timestamps
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', pattern)

        # Replace game tick numbers (e.g., "232945.436")
        pattern = re.sub(r'\s\d+\.\d{3}\s', ' <TICK> ', pattern)

        # Replace entity names (e.g., "zombieFemaleFat", "zombieMoe", "animalChicken")
        # This catches zombie*, animal*, vehicle*, player* followed by a capitalized name
        pattern = re.sub(r'\b(zombie|animal|vehicle|player|entity)([A-Z][a-zA-Z0-9]*)\b', r'\1<NAME>', pattern)

        # Replace counter numbers (e.g., "#10", "#0")
        pattern = re.sub(r'#\d+', '#<NUM>', pattern)

        # Replace IDs (e.g., "id 167772", "id=12345")
        pattern = re.sub(r'\bid[=\s]+\d+', 'id=<NUM>', pattern)

        # Replace 3D coordinates (e.g., "(109.8, 42.8, 782.6)")
        pattern = re.sub(r'\(-?\d+\.\d+,\s*-?\d+\.\d+,\s*-?\d+\.\d+\)', '(<COORD>)', pattern)

        # Replace chunk coordinates (e.g., "chunk 6, 48")
        pattern = re.sub(r'chunk\s+-?\d+,\s*-?\d+', 'chunk <CHUNK>', pattern)

        # Replace entity IDs (e.g., "entityid=12345")
        pattern = re.sub(r'entityid=\d+', 'entityid=<NUM>', pattern)

        # Replace generic numbers in context (e.g., "killed 5 zombies" -> "killed <NUM> zombies")
        pattern = re.sub(r'\b\d+\b', '<NUM>', pattern)

        return pattern

    @staticmethod
    def _generate_pattern_id(pattern: str) -> str:
        """Generate a unique ID for a pattern using hash."""
        return hashlib.md5(pattern.encode()).hexdigest()[:12]

    def _store_unmatched_telnet_line(self, telnet_line: str) -> None:
        """Store unmatched telnet line - first occurrence only, no counting."""
        pattern = self._extract_line_pattern(telnet_line)
        pattern_id = self._generate_pattern_id(pattern)

        # Only store if this pattern is NEW (first occurrence)
        if pattern_id not in self.unmatched_patterns_dict:
            current_time = time()
            pattern_data = {
                "id": pattern_id,
                "pattern": pattern,
                "example_line": telnet_line,
                "first_seen": current_time,
                "is_selected": False
            }

            # Store by pattern_id (not pattern string)
            self.unmatched_patterns_dict[pattern_id] = pattern_data

            # Update DOM for persistence (upsert single pattern)
            self.dom.data.upsert({
                self.get_module_identifier(): {
                    "unmatched_patterns": {
                        pattern_id: pattern_data
                    }
                }
            })

            # Emit new pattern for real-time prepend to widget
            self.dom.data.append({
                self.get_module_identifier(): {
                    "new_unmatched_pattern": pattern_data
                }
            }, maxlen=1)

    def execute_telnet_triggers(self):
        telnet_lines_to_process = self.telnet.get_a_bunch_of_lines_from_queue(25)

        for telnet_line in telnet_lines_to_process:
            line_matched = False

            for loaded_module in loaded_modules_dict.values():
                for trigger_name, trigger_group in loaded_module.available_triggers_dict.items():
                    try:
                        for trigger in trigger_group["triggers"]:
                            regex_results = re.search(trigger["regex"], telnet_line)
                            if regex_results:
                                trigger["callback"](loaded_module, self, regex_results)
                                line_matched = True
                                # TODO: this needs to weed out triggers being called too often
                    except KeyError:
                        pass

            # Store unmatched lines for trigger development
            if not line_matched:
                self._store_unmatched_telnet_line(telnet_line)
