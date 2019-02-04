from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, dispatchers_steamid=None):
    webserver_logged_in_users = module.dom.data.get(module.get_module_identifier(), {}).get("webserver_logged_in_users", {})

    try:
        server_is_online = module.dom.data.get("module_telnet").get("server_is_online", True)
    except AttributeError as error:
        server_is_online = True

    template_frontend = module.templates.get_template('webserver_status_widget_frontend.html')
    data_to_emit = template_frontend.render(
        webserver_logged_in_users=webserver_logged_in_users,
        server_is_online=server_is_online
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=webserver_logged_in_users.keys(),
        target_element={
            "id": "webserver_status_widget",
            "type": "div",
            "selector": "body > main > div"
        }
    )


def update_widget(module, updated_values_dict=None, old_values_dict=None):
    webserver_logged_in_users = updated_values_dict.get("webserver_logged_in_users", {})
    old_webserver_logged_in_users = old_values_dict.get("webserver_logged_in_users", {})
    if webserver_logged_in_users == old_webserver_logged_in_users:
        return

    template_frontend = module.templates.get_template('webserver_status_widget_frontend.html')
    data_to_emit = template_frontend.render(
        webserver_logged_in_users=webserver_logged_in_users,
        server_is_online=module.dom.data.get("module_telnet").get("server_is_online")
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "webserver_status_widget",
            "type": "div",
            "selector": "body > main > div"
        }
    )


widget_meta = {
    "description": "sends and updates a table of all currently known players",
    "main_widget": main_widget,
    "handlers": {
        "module_environment/webserver_logged_in_users": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
