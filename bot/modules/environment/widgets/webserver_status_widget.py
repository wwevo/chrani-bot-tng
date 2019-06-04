from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, dispatchers_steamid=None):
    webserver_logged_in_users = module.dom.data.get(module.get_module_identifier(), {}).get("webserver_logged_in_users", {})

    try:
        server_is_online = module.dom.data.get("module_telnet").get("server_is_online", True)
    except AttributeError as error:
        server_is_online = True

    template_frontend = module.templates.get_template('webserver_status_widget/view_frontend.html')
    template_servertime = module.templates.get_template('webserver_status_widget/control_servertime.html')
    data_to_emit = template_frontend.render(
        webserver_logged_in_users=webserver_logged_in_users,
        servertime=template_servertime.render(
            time=module.dom.data.get("module_telnet").get("last_recorded_servertime", None),
        ),
        server_is_online=server_is_online
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=webserver_logged_in_users.keys(),
        target_element={
            "id": "webserver_status_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def update_widget(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    webserver_logged_in_users = updated_values_dict.get("webserver_logged_in_users", {})
    old_webserver_logged_in_users = old_values_dict.get("webserver_logged_in_users", {})

    if webserver_logged_in_users == old_webserver_logged_in_users:
        return

    template_frontend = module.templates.get_template('webserver_status_widget/view_frontend.html')

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
            "type": "table",
            "selector": "body > main > div"
        }
    )


def update_servertime(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    template_servertime = module.templates.get_template('webserver_status_widget/control_servertime.html')
    servertime_view=template_servertime.render(
        time=module.dom.data.get("module_telnet").get("last_recorded_servertime", None)
    )

    module.webserver.send_data_to_client(
        event_data=servertime_view,
        data_type="element_content",
        method="replace",
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "server_status_widget_servertime",
            "type": "div",
            "selector": "body > main > div"
        }
    )


widget_meta = {
    "description": "shows all users with an active session for the webinterface",
    "main_widget": main_widget,
    "handlers": {
        "module_telnet/last_recorded_servertime": update_servertime,
        "module_environment/webserver_logged_in_users": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
