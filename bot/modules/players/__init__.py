from bot.module import Module
from bot import loaded_modules_dict

class Players(Module):
    dom_element_root = list
    dom_element_select_root = list

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "run_observer_interval": 3,
        })

        setattr(self, "required_modules", [
            "module_webserver",
            "module_dom",
            "module_game_environment",
            "module_telnet"
        ])

        self.next_cycle = 0

        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_players"

    def setup(self, options=None):
        Module.setup(self, options)
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )

    # run() is inherited from Module - periodic actions loop runs automatically!

loaded_modules_dict[Players().get_module_identifier()] = Players()
