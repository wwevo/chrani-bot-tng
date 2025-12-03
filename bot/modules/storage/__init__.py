from os import path
from queue import Queue, Empty
from threading import Thread

from bot import loaded_modules_dict
from bot.module import Module
from .persistent_dict import PersistentDict


class Storage(Module):
    root_dir = str
    save_queue = object
    writer_thread = object

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "run_observer_interval": 10,
            "file_name": "storage",
            "file_format": "pickle"
        })

        setattr(self, "required_modules", [
            "module_dom"
        ])

        self.next_cycle = 0
        self.save_queue = Queue()
        self.writer_thread = None
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_storage"

    def setup(self, options=None):
        Module.setup(self, options)
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval")
        )
        self.file_name = self.options.get(
            "file_name", self.default_options.get("file_name")
        )
        self.file_format = self.options.get(
            "file_format", self.default_options.get("file_format")
        )
        self.root_dir = path.dirname(path.abspath(__file__))

    def load_persistent_dict_to_dom(self):
        with PersistentDict(path.join(self.root_dir, "{}.{}".format(self.file_name, self.file_format)), 'c', format=self.file_format) as storage:
            self.dom.data.update(storage)

    def save_dom_to_persistent_dict(self):
        """Non-blocking save: puts data copy in queue for background writer"""
        data_copy = self.dom.data.copy()
        self.save_queue.put(data_copy)

    def _writer_loop(self):
        """Background thread that processes save queue"""
        while not self.stopped.is_set():
            try:
                data = self.save_queue.get(timeout=1)
                with PersistentDict(path.join(self.root_dir, "{}.{}".format(self.file_name, self.file_format)), 'c', format=self.file_format) as storage:
                    storage.update(data)
            except Empty:
                continue

    def on_start(self):
        self.load_persistent_dict_to_dom()
        # Start background writer thread
        self.writer_thread = Thread(target=self._writer_loop, daemon=True)
        self.writer_thread.start()

    # run() is inherited from Module - periodic actions loop runs automatically!

loaded_modules_dict[Storage().get_module_identifier()] = Storage()
