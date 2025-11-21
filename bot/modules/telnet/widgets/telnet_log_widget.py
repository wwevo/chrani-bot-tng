from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


# View Registry (mirrors locations menu pattern, but only one visible button here)
VIEW_REGISTRY = {
    'frontend': {
        'label_active': 'back',
        'label_inactive': 'main',
        'action': 'show_frontend',
        'include_in_menu': False
    },
    'options': {
        'label_active': 'back',
        'label_inactive': 'options',
        'action': 'show_options',
        'include_in_menu': True
    },
    'test': {
        'label_active': 'back',
        'label_inactive': 'patterns',
        'action': 'show_test',
        'include_in_menu': True
    }
}


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
    current_view = module.get_current_view(dispatchers_steamid)
    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    elif current_view == "test":
        test_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    telnet_log_frontend = module.templates.get_template('telnet_log_widget/view_frontend.html')
    template_table_header = module.templates.get_template('telnet_log_widget/table_header.html')
    log_line = module.templates.get_template('telnet_log_widget/log_line.html')

    # new view menu (pattern from locations module)
    template_view_menu = module.templates.get_template('telnet_log_widget/control_view_menu.html')

    if len(module.webserver.connected_clients) >= 1:
        telnet_lines = module.dom.data.get("module_telnet", {}).get("telnet_lines", {})
        if len(telnet_lines) >= 1:
            # Build log lines efficiently using list comprehension
            log_lines_list = []
            for line in reversed(telnet_lines):
                css_class = get_log_line_css_class(line)
                log_lines_list.append(module.template_render_hook(
                    module,
                    template=log_line,
                    log_line=line,
                    css_class=css_class
                ))
            log_lines = ''.join(log_lines_list)

            current_view = module.get_current_view(dispatchers_steamid)
            options_toggle = module.template_render_hook(
                module,
                template=template_view_menu,
                views=VIEW_REGISTRY,
                current_view=current_view,
                steamid=dispatchers_steamid
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
    template_view_menu = module.templates.get_template('telnet_log_widget/control_view_menu.html')

    current_view = module.get_current_view(dispatchers_steamid)
    options_toggle = module.template_render_hook(
        module,
        template=template_view_menu,
        views=VIEW_REGISTRY,
        current_view=current_view,
        steamid=dispatchers_steamid
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


def test_view(*args, **kwargs):
    """Initial view load - shows all existing patterns. Granular updates handled separately."""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_test = module.templates.get_template('telnet_log_widget/view_test.html')
    template_view_menu = module.templates.get_template('telnet_log_widget/control_view_menu.html')
    pattern_line = module.templates.get_template('telnet_log_widget/pattern_line.html')

    if len(module.webserver.connected_clients) >= 1:
        unmatched_patterns = module.dom.data.get("module_game_environment", {}).get("unmatched_patterns", {})

        # Build pattern lines from DOM structure {pattern_id: pattern_data}
        pattern_lines_list = []
        if len(unmatched_patterns) >= 1:
            # Sort patterns by first_seen (newest first)
            sorted_patterns = sorted(
                unmatched_patterns.items(),
                key=lambda x: x[1].get("first_seen", 0),
                reverse=True
            )

            for pattern_id, pattern_data in sorted_patterns:
                pattern_lines_list.append(module.template_render_hook(
                    module,
                    template=pattern_line,
                    pattern_id=pattern_id,
                    pattern=pattern_data.get("pattern", ""),
                    example_line=pattern_data.get("example_line", ""),
                    is_selected=pattern_data.get("is_selected", False)
                ))

        pattern_lines = ''.join(pattern_lines_list) if pattern_lines_list else '<tr><td colspan="3">No unmatched patterns yet...</td></tr>'

        current_view = module.get_current_view(dispatchers_steamid)
        options_toggle = module.template_render_hook(
            module,
            template=template_view_menu,
            views=VIEW_REGISTRY,
            current_view=current_view,
            steamid=dispatchers_steamid
        )

        data_to_emit = module.template_render_hook(
            module,
            template=template_test,
            options_toggle=options_toggle,
            pattern_lines=pattern_lines
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

    # Iterate directly over connected clients (no need to convert to list)
    for clientid in module.webserver.connected_clients.keys():
        current_view = module.get_current_view(clientid)
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


def add_new_pattern(*args, **kwargs):
    """Prepend new pattern to list - granular update, no full reload."""
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    pattern_data = updated_values_dict.get("new_unmatched_pattern", None)
    if pattern_data is None:
        return

    pattern_line = module.templates.get_template('telnet_log_widget/pattern_line.html')

    for clientid in module.webserver.connected_clients.keys():
        current_view = module.get_current_view(clientid)
        if current_view == "test":
            data_to_emit = module.template_render_hook(
                module,
                template=pattern_line,
                pattern_id=pattern_data.get("id", "unknown"),
                pattern=pattern_data.get("pattern", ""),
                example_line=pattern_data.get("example_line", ""),
                is_selected=pattern_data.get("is_selected", False)
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


def update_pattern_selection(*args, **kwargs):
    """Update single pattern row when selection changes - granular update."""
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    # Extract pattern_id from updated_values_dict path
    # The path will be like: unmatched_patterns -> pattern_id -> is_selected
    pattern_id = list(updated_values_dict.get("unmatched_patterns", {}).keys())[0] if updated_values_dict else None

    if pattern_id is None:
        return

    pattern_data = updated_values_dict["unmatched_patterns"][pattern_id]
    pattern_line = module.templates.get_template('telnet_log_widget/pattern_line.html')

    # Get full pattern data from DOM
    full_pattern_data = module.dom.data.get("module_game_environment", {}).get("unmatched_patterns", {}).get(pattern_id, {})

    for clientid in module.webserver.connected_clients.keys():
        current_view = module.get_current_view(clientid)
        if current_view == "test":
            data_to_emit = module.template_render_hook(
                module,
                template=pattern_line,
                pattern_id=pattern_id,
                pattern=full_pattern_data.get("pattern", ""),
                example_line=full_pattern_data.get("example_line", ""),
                is_selected=full_pattern_data.get("is_selected", False)
            )

            module.webserver.send_data_to_client_hook(
                module,
                method="update",
                data_type="widget_content",
                payload=data_to_emit,
                clients=[clientid],
                target_element={
                    "id": "pattern_" + pattern_id,
                    "type": "table_row",
                    "selector": "body > main > div"
                }
            )


widget_meta = {
    "description": "displays a bunch of telnet lines, updating in real time",
    "main_widget": select_view,
    "handlers": {
        "module_telnet/visibility/%steamid%/current_view": select_view,
        "module_telnet/telnet_lines": update_widget,
        "module_game_environment/new_unmatched_pattern": add_new_pattern,
        "module_game_environment/unmatched_patterns/%pattern_id%": update_pattern_selection,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
