from bot.module import Module
from bot import loaded_modules_dict


class Testing(Module):
    dom_element_root = list
    dom_element_select_root = list

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "dom_element_root": [],
            "dom_element_select_root": ["id"],
            "test_steamid_prefix": "76561198999",
            "test_location_prefix": "test_",
            "test_dataset_prefix": "TestWorld_",
            "run_observer_interval": 3,
            "run_observer_interval_idle": 10
        })

        setattr(self, "required_modules", [
            'module_dom',
            'module_dom_management',
            'module_telnet',
            'module_webserver'
        ])

        self.next_cycle = 0
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_testing"

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

    def start(self):
        """ all modules have been loaded and initialized by now. we can bend the rules here."""
        Module.start(self)
    # endregion

    def run(self):
        # This module doesn't need a run loop
        pass


loaded_modules_dict[Testing().get_module_identifier()] = Testing()
