from modules.module import Module
from modules import loaded_modules_dict
from time import time


class Environment(Module):
    run_observer_interval = int
    last_execution_time = float

    # region Standard module stuff
    def __init__(self):
        setattr(self, "default_options", {
            "module_name": "environment"
        })

        setattr(self, "required_modules", [
            "module_dom",
            "module_telnet",
            "module_webserver"
        ])
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_environment"

    def setup(self, options=dict):
        Module.setup(self, options)
        self.run_observer_interval = 2
        return self

    def start(self):
        Module.start(self)
        return self
    # endregion

    def run(self):
        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()
            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Environment().get_module_identifier()] = Environment()
