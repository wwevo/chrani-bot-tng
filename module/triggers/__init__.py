from module.module import Module
from module import loaded_modules_dict
from time import time
import re


class Triggers(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })
        setattr(self, "required_modules", [
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
        self.run_observer_interval = 0.25
    # endregion

    def run(self):
        available_triggers_dict = {}
        for loaded_module in loaded_modules_dict.values():
            available_triggers_dict.update(loaded_module.available_triggers_dict)

        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()

            telnet_lines_to_process = self.telnet.get_a_bunch_of_lines(25)
            for telnet_line in telnet_lines_to_process:
                for trigger_name, trigger in available_triggers_dict.items():
                    for regex in trigger["regex"]:
                        regex_results = re.search(regex, telnet_line)
                        if regex_results:
                            trigger["main_function"](self, regex_results)
                            message = "executed trigger: {}".format(trigger_name)
                            print(message)
                            if len(self.webserver.connected_clients) >= 1:
                                self.telnet.update_telnet_log_widget_log_line(message)

            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Triggers().get_module_identifier()] = Triggers()
