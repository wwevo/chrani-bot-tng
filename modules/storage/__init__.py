from modules.module import Module
from modules import loaded_modules_dict
from time import time
from .persistent_dict import PersistentDict
from os import path


class Storage(Module):
    root_dir = str

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })
        setattr(self, "required_modules", [
            "module_dom"
        ])
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_storage"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
        self.run_observer_interval = 15
    # endregion

    def run(self):
        self.root_dir = path.dirname(path.abspath(__file__))
        with PersistentDict(path.join(self.root_dir, "storage"), 'c') as storage:
            self.dom.data.update(storage)

        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()

            with PersistentDict(path.join(self.root_dir, "storage"), 'c') as storage:
                storage.update(self.dom.data)

            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Storage().get_module_identifier()] = Storage()
