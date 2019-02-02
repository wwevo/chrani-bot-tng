from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, updated_values_dict=None, old_values_dict=None):
    template_frontend = module.templates.get_template('gameserver_status_widget_frontend.html')

    server_is_online = module.dom.data.get("module_telnet").get("server_is_online", False)
    shutdown_in_seconds = module.dom.data.get("module_telnet").get("shutdown_in_seconds", None)

    data_to_emit = template_frontend.render(
        server_is_online=server_is_online,
        shutdown_in_seconds=shutdown_in_seconds
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "gameserver_status_widget",
            "type": "div"
        }
    )


widget_meta = {
    "description": "shows gameserver status, shut it down. or don't ^^",
    "main_widget": main_widget,
    "handlers": {
        "server_is_online": main_widget,
        "shutdown_in_seconds": main_widget,
        "cancel_shutdown": main_widget,
        "force_shutdown": main_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
