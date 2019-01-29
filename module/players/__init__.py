from module.module import Module
from module import loaded_modules_dict
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
            in_limbo = player_dict["in_limbo"]
            is_online = player_dict["is_online"]

            if in_limbo and is_online:
                css_class = "is_online in_limbo"
            elif not in_limbo and is_online:
                css_class = "is_online"
            elif in_limbo and not is_online:
                css_class = "is_offline in_limbo"
            else:
                css_class = ""

            if steamid == 'last_updated':
                continue

            table_rows += template_table_rows.render(
                player=player_dict,
                css_class=css_class
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
                "type": "table",
            }
        )

    def update_player_table_widget_table_row(self, player_dict):
        in_limbo = player_dict["in_limbo"]
        is_online = player_dict["is_online"]

        if in_limbo and is_online:
            css_class = "is_online in_limbo"
        if in_limbo and not is_online:
            css_class = "is_offline in_limbo"
        if not in_limbo and is_online:
            css_class = "is_online"
        if not in_limbo and not is_online:
            css_class = "is_offline"

        template_table_rows = self.templates.get_template('player_table_widget_table_row.html')

        table_row = template_table_rows.render(
            player=player_dict,
            css_class=css_class
        )

        self.webserver.send_data_to_client(
            event_data=table_row,
            data_type="widget_content",
            clients=self.webserver.connected_clients.keys(),
            method="update",
            target_element={
                "id": "player_table_row_{}".format(player_dict["steamid"]),
                "selector": "#player_table_widget > tbody",
                "type": "tr",
                "class": css_class
            }
        )

    def update_player_table_widget_data(self, player_dict):
        in_limbo = player_dict["in_limbo"]
        is_online = player_dict["is_online"]

        if in_limbo and is_online:
            css_class = "is_online in_limbo"
        elif not in_limbo and is_online:
            css_class = "is_online"
        elif in_limbo and not is_online:
            css_class = "is_offline in_limbo"
        else:
            css_class = ""

        self.webserver.send_data_to_client(
            event_data=player_dict,
            data_type="element_content",
            clients=self.webserver.connected_clients.keys(),
            method="update",
            target_element={
                "id": "player_table_row_{}".format(player_dict["steamid"]),
                "class": css_class
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
