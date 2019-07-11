from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, dispatchers_steamid=None):
    telnet_log_frontend = module.templates.get_template('telnet_log_widget/view_frontend.html')
    template_table_header = module.templates.get_template('telnet_log_widget/table_header.html')
    log_line = module.templates.get_template('telnet_log_widget/log_line.html')

    if len(module.webserver.connected_clients) >= 1:
        log_lines = ""
        telnet_lines = module.dom.data.get("module_telnet", {}).get("telnet_lines", {})
        if len(telnet_lines) >= 1:
            for line in reversed(telnet_lines):
                log_lines += module.template_render_hook(
                    module,
                    log_line,
                    log_line=line
                )

        data_to_emit = module.template_render_hook(
            module,
            telnet_log_frontend,
            log_lines=log_lines,
            table_header=module.template_render_hook(
                module,
                template_table_header
            )
        )
        module.webserver.send_data_to_client_hook(
            module,
            event_data=data_to_emit,
            data_type="widget_content",
            clients=[dispatchers_steamid],
            method="update",
            target_element={
                "id": "telnet_log_widget",
                "type": "table",
                "selector": "body > main > div"
            }
        )


def update_widget(module, updated_values_dict=None, old_values_dict=None, original_values_dict=None, dispatchers_steamid=None):
    telnet_log_line = module.templates.get_template('telnet_log_widget/log_line.html')

    data_to_emit = module.template_render_hook(
        module,
        telnet_log_line,
        log_line=updated_values_dict["telnet_lines"]
    )

    module.webserver.send_data_to_client_hook(
        module,
        method="prepend",
        data_type="widget_content",
        event_data=data_to_emit,
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "telnet_log_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


widget_meta = {
    "description": "displays a bunch of telnet lines, updating in real time",
    "main_widget": main_widget,
    "handlers": {
        "module_telnet/telnet_lines": update_widget,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
