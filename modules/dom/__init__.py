from modules import loaded_modules_list
from time import time
from threading import Thread, Event


class Dom(Thread):
    options = dict

    stopped = object

    run_observer_interval = int  # loop this every run_observers_interval seconds
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
        self.options = self.default_options
        if isinstance(options, dict):
            print("Dom: provided options have been set")
            self.options.update(options)
        else:
            print("Dom: no options provided, default values are used")

        self.run_observer_interval = 10
        return self

    def start(self):
        self.setDaemon(daemonic=True)
        Thread.start(self)
        return self

    def run(self):
        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()

            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_list.append(Dom())
