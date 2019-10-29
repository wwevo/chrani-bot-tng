from bot.module import Module
from bot import loaded_modules_dict
from time import time


class Players(Module):
    templates = object

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "run_observer_interval": 2,
            "run_observer_interval_idle": 10,
        })

        setattr(self, "required_modules", [
            "module_webserver",
            "module_dom",
            "module_dom_management",
            "module_telnet"
        ])

        self.next_cycle = 0
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_players"

    def on_socket_connect(self, steamid):
        Module.on_socket_connect(self, steamid)

    def on_socket_disconnect(self, steamid):
        Module.on_socket_disconnect(self, steamid)

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)

        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )
        self.run_observer_interval_idle = self.options.get(
            "run_observer_interval_idle",self.default_options.get("run_observer_interval_idle", None)
        )
    # endregion

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.trigger_action_hook(self, ["listadmins", {
                "disable_after_success": True
            }])
            self.trigger_action_hook(self, ["listplayers", {}])

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Players().get_module_identifier()] = Players()
