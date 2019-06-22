from bot.module import Module
from bot import loaded_modules_dict
from time import time


class Locations(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })

        setattr(self, "required_modules", [
            'module_dom',
            'module_players',
            'module_webserver'
        ])

        self.next_cycle = 0
        self.run_observer_interval = 5
        self.all_available_actions_dict = {}
        self.all_available_widgets_dict = {}
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_locations"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion

    def start(self):
        """ all modules have been loaded and initialized by now. we can bend the rules here."""
        Module.start(self)
    # endregion

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Locations().get_module_identifier()] = Locations()
