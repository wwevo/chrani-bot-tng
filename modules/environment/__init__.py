from modules.module import Module
from modules import loaded_modules_dict
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
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_environment"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
        self.run_observer_interval = 1
        return self

    def start(self):
        Module.start(self)
        return self
    # endregion

    def run(self):
        next_cycle = 0
        template_frontend = self.templates.get_template('frontend.html')
        while not self.stopped.wait(next_cycle):
            profile_start = time()

            self.dom.upsert({
                self.get_module_identifier(): {
                    "webserver_logged_in_users": len(self.webserver.connected_clients)
                }
            })

            data_to_emit = template_frontend.render(
                webserver_logged_in_users=self.dom.data.get(self.get_module_identifier()).get("webserver_logged_in_users"),
                server_is_online=("online" if self.dom.data.get("module_telnet").get("server_is_online") else "offline")
            )

            self.webserver.send_data_to_client(
                data=data_to_emit,
                clients=self.webserver.connected_clients.keys(),
                target_element="widget_environment_data"
            )

            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Environment().get_module_identifier()] = Environment()
