from bot.module import Module
from bot import loaded_modules_dict


class Testing(Module):
    """
    Testing module for injecting test data and simulating game events.

    This module provides:
    - Telnet line injection for simulating game events
    - Helper actions for common test scenarios
    - Template library for pre-defined test cases
    - Auto-cleanup based on naming conventions

    Test Data Naming Conventions:
    - SteamIDs: 76561198999xxxxxx (prefix 999)
    - Locations: test_* (prefix test_)
    - Datasets: TestWorld_* (prefix TestWorld_)
    """

    # DOM structure for this module
    dom_element_root = []
    dom_element_select_root = ["id"]

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "test_steamid_prefix": "76561198999",  # Prefix for test SteamIDs
            "test_location_prefix": "test_",        # Prefix for test locations
            "test_dataset_prefix": "TestWorld_",    # Prefix for test datasets
        })

        setattr(self, "required_modules", [
            "module_dom",
            "module_telnet",
            "module_webserver"
        ])

        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_testing"

    def setup(self, options=dict):
        Module.setup(self, options)

    def start(self):
        Module.start(self)

        # Initialize DOM structure
        self.dom.data.upsert({
            self.get_module_identifier(): {
                "last_injected_line": None,
                "injection_count": 0,
                "scenarios_loaded": []
            }
        })

    def run(self):
        # This module doesn't need a run loop, it's purely action-based
        pass


loaded_modules_dict[Testing().get_module_identifier()] = Testing()
