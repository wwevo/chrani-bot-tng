from bot.module import Module
from bot import loaded_modules_dict
from time import time


class Environment(Module):
    templates = object

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })

        setattr(self, "required_modules", [
            "module_dom",
            "module_telnet",
            "module_webserver"
        ])

        self.next_cycle = 0
        self.run_observer_interval = 3
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_environment"

    def on_socket_connect(self, steamid):
        Module.on_socket_connect(self, steamid)

    def on_socket_disconnect(self, steamid):
        Module.on_socket_disconnect(self, steamid)

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion

    def run(self):
        while not self.stopped.wait(self.next_cycle):
            profile_start = time()

            self.trigger_action_hook(self, ["getgamestats", {
                "execute_only_once": True
            }])
            self.trigger_action_hook(self, ["getgameprefs", {
                "execute_only_once": True
            }])
            self.trigger_action_hook(self, ["gettime", {}])

            self.execute_telnet_triggers()

            self.last_execution_time = time() - profile_start
            self.next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Environment().get_module_identifier()] = Environment()
