from modules.module import Module
from modules import loaded_modules_dict
from time import time
from collections import Mapping


class Dom(Module):
    data = dict

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })
        setattr(self, "required_modules", [])
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_dom"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
        self.data = {}
        self.run_observer_interval = 2
        return self

    def start(self):
        Module.start(self)
        return self
    # endregion

    def upsert(self, updated_values_dict, dict_to_update=None):
        if dict_to_update is None:
            dict_to_update = self.data

        for k, v in updated_values_dict.items():
            d_v = dict_to_update.get(k)
            if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                self.upsert(v, d_v)
            else:
                dict_to_update[k] = v  # or d[k] = v if you know what you're doing

        return dict_to_update

    def run(self):
        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()
            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Dom().get_module_identifier()] = Dom()
