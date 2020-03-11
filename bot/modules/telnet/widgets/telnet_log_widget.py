from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_log_line_css_class(log_line):
    css_classes = [
        "log_line"
    ]

    if r"INF Chat" in log_line:
        css_classes.append("game_chat")
    if r"(BCM) Command from" in log_line:
        css_classes.append("bot_command")
    if any([
        r"joined the game" in log_line,
        r"left the game" in log_line
    ]):
        css_classes.append("player_logged")

    return " ".join(css_classes)


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = (
        module.dom.data
        .get("module_telnet", {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view", "frontend")
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    telnet_log_frontend = module.templates.get_template('telnet_log_widget/view_frontend.html')
    template_table_header = module.templates.get_template('telnet_log_widget/table_header.html')
    log_line = module.templates.get_template('telnet_log_widget/log_line.html')

    template_options_toggle = module.templates.get_template('telnet_log_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('telnet_log_widget/control_switch_options_view.html')

    if len(module.webserver.connected_clients) >= 1:
        log_lines = ""
        telnet_lines = module.dom.data.get("module_telnet", {}).get("telnet_lines", {})
        if len(telnet_lines) >= 1:
            for line in reversed(telnet_lines):
                css_class = get_log_line_css_class(line)
                log_lines += module.template_render_hook(
                    module,
                    template=log_line,
                    log_line=line,
                    css_class=css_class
                )

            current_view = (
                module.dom.data
                .get("module_telnet", {})
                .get("visibility", {})
                .get(dispatchers_steamid, {})
                .get("current_view", "frontend")
            )

            options_toggle = module.template_render_hook(
                module,
                template=template_options_toggle,
                control_switch_options_view=module.template_render_hook(
                    module,
                    template=template_options_toggle_view,
                    options_view_toggle=(True if current_view == "frontend" else False),
                    steamid=dispatchers_steamid
                )
            )
            data_to_emit = module.template_render_hook(
                module,
                template=telnet_log_frontend,
                options_toggle=options_toggle,
                log_lines=log_lines,
                table_header=module.template_render_hook(
                    module,
                    template=template_table_header
                )
            )
            module.webserver.send_data_to_client_hook(
                module,
                payload=data_to_emit,
                data_type="widget_content",
                clients=[dispatchers_steamid],
                method="update",
                target_element={
                    "id": "telnet_log_widget",
                    "type": "table",
                    "selector": "body > main > div"
                }
            )


def options_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_frontend = module.templates.get_template('telnet_log_widget/view_options.html')
    template_options_toggle = module.templates.get_template('telnet_log_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('telnet_log_widget/control_switch_options_view.html')

    current_view = (
        module.dom.data
        .get("module_telnet", {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view", "frontend")
    )

    options_toggle = module.template_render_hook(
        module,
        template_options_toggle,
        control_switch_options_view=module.template_render_hook(
            module,
            template=template_options_toggle_view,
            options_view_toggle=(True if current_view == "frontend" else False),
            steamid=dispatchers_steamid
        )
    )

    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        options_toggle=options_toggle,
        widget_options=module.options
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "telnet_log_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def update_widget(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    player_clients_to_update = list(module.webserver.connected_clients.keys())
    for clientid in player_clients_to_update:
        current_view = (
            module.dom.data
            .get("module_telnet", {})
            .get("visibility", {})
            .get(clientid, {})
            .get("current_view", "frontend")
        )

        if current_view == "frontend":
            telnet_log_line = module.templates.get_template('telnet_log_widget/log_line.html')
            css_class = get_log_line_css_class(updated_values_dict["telnet_lines"])
            data_to_emit = module.template_render_hook(
                module,
                template=telnet_log_line,
                log_line=updated_values_dict["telnet_lines"],
                css_class=css_class
            )

            module.webserver.send_data_to_client_hook(
                module,
                method="prepend",
                data_type="widget_content",
                payload=data_to_emit,
                clients=[clientid],
                target_element={
                    "id": "telnet_log_widget",
                    "type": "table",
                    "selector": "body > main > div"
                }
            )


widget_meta = {
    "description": "displays a bunch of telnet lines, updating in real time",
    "main_widget": select_view,
    "handlers": {
        "module_telnet/visibility/%steamid%/current_view": select_view,
        "module_telnet/telnet_lines": update_widget,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
