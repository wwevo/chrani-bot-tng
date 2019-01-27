from modules.module import Module
from modules import loaded_modules_dict
from time import time


class Players(Module):
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
        return "module_players"

    def on_socket_connect(self, steamid):
        Module.on_socket_connect(self, steamid)
        self.update_player_table_widget_frontend()

    def on_socket_disconnect(self, steamid):
        Module.on_socket_disconnect(self, steamid)
        self.update_player_table_widget_frontend()

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
        self.run_observer_interval = 1.5
    # endregion

    def update_player_table_widget_frontend(self):
        template_frontend = self.templates.get_template('player_table_widget_frontend.html')
        template_table_rows = self.templates.get_template('player_table_widget_table_row.html')

        all_player_dicts = self.dom.data.get(self.get_module_identifier(), {}).get("players", {})
        table_rows = ""
        for steamid, player_dict in all_player_dicts.items():
            if steamid == 'last_updated':
                continue

            table_rows += template_table_rows.render(
                player=player_dict
            )

        data_to_emit = template_frontend.render(
            table_rows=table_rows
        )

        self.webserver.send_data_to_client(
            event_data=data_to_emit,
            data_type="widget_content",
            clients=self.webserver.connected_clients.keys(),
            method="update",
            target_element={
                "id": "player_table_widget",
                "type": "table"
            }
        )

    def update_player_table_widget_table_row(self, steamid):
        template_table_rows = self.templates.get_template('player_table_widget_table_row.html')

        player_dict = self.dom.data.get(self.get_module_identifier(), {}).get("players", {}).get(steamid, {})
        table_row = template_table_rows.render(
            player=player_dict
        )

        self.webserver.send_data_to_client(
            event_data=table_row,
            data_type="widget_table_row",
            clients=self.webserver.connected_clients.keys(),
            method="update",
            target_element={
                "id": "player_table_row_{}".format(steamid),
                "parent_table": "player_table_widget",
                "type": "tr"
            }
        )

    def run(self):
        next_cycle = 0
        while not self.stopped.wait(next_cycle):
            profile_start = time()

            self.manually_trigger_event(["listplayers", {}])

            self.last_execution_time = time() - profile_start
            next_cycle = self.run_observer_interval - self.last_execution_time


loaded_modules_dict[Players().get_module_identifier()] = Players()
