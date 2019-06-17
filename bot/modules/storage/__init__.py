from os import path
from time import time
from bot.module import Module
from bot import loaded_modules_dict
from .persistent_dict import PersistentDict


class Storage(Module):
    root_dir = str

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })

        setattr(self, "required_modules", [
            "module_dom"
        ])

        self.next_cycle = 0
        self.run_observer_interval = 15
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_storage"

    def load_persistent_dict_to_dom(self):
        with PersistentDict(path.join(self.root_dir, "storage"), 'c') as storage:
            self.dom.data.update(storage)

    def save_dom_to_persistent_dict(self):
        with PersistentDict(path.join(self.root_dir, "storage"), 'c') as storage:
            storage.update(self.dom.data)

    # region Standard module stuff
    def setup(self, options=dict):
        self.root_dir = path.dirname(path.abspath(__file__))
        Module.setup(self, options)

    def start(self):
        Module.start(self)
        self.load_persistent_dict_to_dom()
    # endregion

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.save_dom_to_persistent_dict()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Storage().get_module_identifier()] = Storage()
