from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module):
    telnet_log_frontend = module.templates.get_template('telnet_log_widget_frontend.html')
    log_line = module.templates.get_template('telnet_log_widget_log_line.html')

    if len(module.webserver.connected_clients) >= 1:
        log_lines = ""
        for line in module.telnet.valid_telnet_lines:
            log_lines += log_line.render(
                log_line=line
            )

        data_to_emit = telnet_log_frontend.render(
            log_lines=log_lines
        )
        module.webserver.send_data_to_client(
            event_data=data_to_emit,
            data_type="widget_content",
            clients=module.webserver.connected_clients.keys(),
            method="update",
            target_element={
                "id": "telnet_log_widget",
                "type": "ul"
            }
        )


def update_widget(module, updated_values_dict, old_values_dict):
    telnet_log_line = module.templates.get_template('telnet_log_widget_log_line.html')

    data_to_emit = telnet_log_line.render(
        log_line=updated_values_dict["telnet_lines"]
    )

    module.webserver.send_data_to_client(
        method="prepend",
        data_type="widget_content",
        event_data=data_to_emit,
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "telnet_log_widget",
            "type": "ul"
        }
    )


widget_meta = {
    "description": "sends and updates a table of all currently known players",
    "main_widget": main_widget,
    "handlers": {
        "module_telnet/telnet_lines": update_widget,
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
