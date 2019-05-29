from bot.module import Module
from bot import loaded_modules_dict
from time import time
import re


class Triggers(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })
        self.next_cycle = 0
        self.run_observer_interval = 0.25
        setattr(self, "required_modules", [
            "module_dom",
            "module_telnet",
            "module_webserver"
        ])
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_triggers"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

    def start(self):
        Module.start(self)
    # endregion

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            telnet_lines_to_process = self.telnet.get_a_bunch_of_lines(25)
            for telnet_line in telnet_lines_to_process:
                for loaded_module in loaded_modules_dict.values():
                    for trigger_name, trigger in loaded_module.available_triggers_dict.items():
                        for sub_trigger in trigger["triggers"]:
                            regex_results = re.search(sub_trigger["regex"], telnet_line)
                            if regex_results:
                                sub_trigger["callback"](self, regex_results)
                                message = "executed trigger: {}".format(trigger_name)
                                # print(message)
                                if len(self.webserver.connected_clients) >= 1:
                                    # TODO: add method to append log, or create a new one
                                    pass

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Triggers().get_module_identifier()] = Triggers()
