from os import path

from bot import loaded_modules_dict
from bot.module import Module
from .persistent_dict import PersistentDict


class Storage(Module):
    root_dir = str

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "run_observer_interval": 10
        })

        setattr(self, "required_modules", [
            "module_dom"
        ])

        self.next_cycle = 0
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_storage"

    def setup(self, options=None):
        Module.setup(self, options)
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        self.root_dir = path.dirname(path.abspath(__file__))

    def load_persistent_dict_to_dom(self):
        with PersistentDict(path.join(self.root_dir, "storage.pickle"), 'c', format="pickle") as storage:
            self.dom.data.update(storage)

    def save_dom_to_persistent_dict(self):
        with PersistentDict(path.join(self.root_dir, "storage.pickle"), 'c', format="pickle") as storage:
            storage.update(self.dom.data)

    def on_start(self):
        self.load_persistent_dict_to_dom()

    # run() is inherited from Module - periodic actions loop runs automatically!

loaded_modules_dict[Storage().get_module_identifier()] = Storage()
