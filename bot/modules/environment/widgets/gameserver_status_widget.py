from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('gameserver_status_widget_frontend.html')

    server_is_online = module.dom.data.get("module_telnet", {}).get("server_is_online", True)
    telnet_data_transfer_is_enabled = module.dom.data.get("module_telnet", {}).get("data_transfer_enabled", True)
    shutdown_in_seconds = module.dom.data.get("module_telnet", {}).get("shutdown_in_seconds", None)
    data_to_emit = template_frontend.render(
        server_is_online=server_is_online,
        shutdown_in_seconds=shutdown_in_seconds,
        data_transfer_enabled=telnet_data_transfer_is_enabled
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "gameserver_status_widget",
            "type": "div",
            "selector": "body > header > div"
        }
    )


def update_widget(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('gameserver_status_widget_frontend.html')

    if updated_values_dict is None:
        try:
            telnet_data_transfer_is_enabled = module.dom.data.get("module_telnet").get("data_transfer_enabled", False)
        except AttributeError as error:
            telnet_data_transfer_is_enabled = False

        try:
            server_is_online = module.dom.data.get("module_telnet").get("server_is_online", True)
        except AttributeError as error:
            server_is_online = True

        try:
            shutdown_in_seconds = module.dom.data.get("module_telnet").get("shutdown_in_seconds")
        except AttributeError as error:
            shutdown_in_seconds = None
    else:
        server_is_online = updated_values_dict.get("server_is_online", True)
        shutdown_in_seconds = updated_values_dict.get("shutdown_in_seconds", None)
        telnet_data_transfer_is_enabled = updated_values_dict.get("data_transfer_enabled", False)

    data_to_emit = template_frontend.render(
        server_is_online=server_is_online,
        shutdown_in_seconds=shutdown_in_seconds,
        data_transfer_enabled=telnet_data_transfer_is_enabled
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "gameserver_status_widget",
            "type": "div",
            "selector": "body > header > div"
        }
    )


widget_meta = {
    "description": "shows gameserver status, shut it down. or don't ^^",
    "main_widget": main_widget,
    "handlers": {
        "module_telnet/server_is_online": update_widget,
        "module_telnet/data_transfer_enabled": update_widget,
        "module_telnet/shutdown_in_seconds": update_widget,
        "module_telnet/cancel_shutdown": update_widget,
        "module_telnet/force_shutdown": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
