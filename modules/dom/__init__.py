from modules import loaded_modules_dict
from time import time
from threading import Thread, Event
from collections import Mapping


class Dom(Thread):
    options = dict

    stopped = object

    data = dict

    run_observer_interval = int
    last_execution_time = float

    def __init__(self):
        self.default_options = {}

        self.stopped = Event()
        Thread.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_dom"

    def setup(self, options=dict):
        self.name = 'dom'
        self.data = {}

        self.options = self.default_options
        if isinstance(options, dict):
            print("Dom: provided options have been set")
            self.options.update(options)
        else:
            print("Dom: no options provided, default values are used")

        self.run_observer_interval = 2
        return self

    def start(self):
        self.setDaemon(daemonic=True)
        Thread.start(self)
        return self

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
