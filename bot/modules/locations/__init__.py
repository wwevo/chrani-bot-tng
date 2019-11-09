from bot.module import Module
from bot import loaded_modules_dict
from time import time


class Locations(Module):
    dom_element_root = list
    dom_element_select_root = list
    default_max_locations = int
    standard_location_shape = str

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "dom_element_root": ["%dom_element_identifier%"],
            "dom_element_select_root": ["%dom_element_identifier%", "selected_by"],
            "default_max_locations": 3,
            "standard_location_shape": "rectangular",
            "run_observer_interval": 5,
            "run_observer_interval_idle": 10
        })

        setattr(self, "required_modules", [
            'module_dom',
            'module_dom_management',
            'module_players',
            'module_webserver'
        ])

        self.next_cycle = 0
        self.all_available_actions_dict = {}
        self.all_available_widgets_dict = {}
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_locations"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        self.run_observer_interval_idle = self.options.get(
            "run_observer_interval_idle", self.default_options.get("run_observer_interval_idle", None)
        )
        self.dom_element_root = self.options.get(
            "dom_element_root", self.default_options.get("dom_element_root", None)
        )
        self.dom_element_select_root = self.options.get(
            "dom_element_select_root", self.default_options.get("dom_element_select_root", None)
        )
        self.default_max_locations = self.options.get(
            "default_max_locations", self.default_options.get("default_max_locations", None)
        )
        self.standard_location_shape = self.options.get(
            "standard_location_shape", self.default_options.get("standard_location_shape", None)
        )
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
