from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('gameserver_status_widget_frontend.html')

    server_is_online = module.dom.data.get("module_telnet", {}).get("server_is_online", True)
    telnet_data_transfer_is_enabled = module.dom.data.get("module_telnet", {}).get("data_transfer_enabled", True)
    shutdown_in_seconds = module.dom.data.get("module_telnet", {}).get("shutdown_in_seconds", None)
    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
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

    telnet_data_transfer_is_enabled = module.dom.get_updated_or_default_value(
        "module_telnet", "data_transfer_enabled", updated_values_dict, False
    )

    server_is_online = module.dom.get_updated_or_default_value(
        "module_telnet", "server_is_online", updated_values_dict, True
    )

    shutdown_in_seconds = module.dom.get_updated_or_default_value(
        "module_telnet", "shutdown_in_seconds", updated_values_dict, None
    )

    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
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
