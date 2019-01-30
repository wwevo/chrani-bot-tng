from module.module import Module
from module import loaded_modules_dict
from time import time
from .callback_dict import CallbackDict


class Dom(Module):
    data = CallbackDict

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })
        setattr(self, "required_modules", [])
        self.data = CallbackDict()
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_dom"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
        self.run_observer_interval = 5
    # endregion

    def run(self):
        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()
            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Dom().get_module_identifier()] = Dom()
