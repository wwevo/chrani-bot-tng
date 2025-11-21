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
        unmatched_patterns_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    telnet_log_frontend = module.templates.get_template('telnet_log_widget/view_telnet_log.html')
    template_table_header = module.templates.get_template('telnet_log_widget/telnet_log_table_header.html')
    log_line = module.templates.get_template('telnet_log_widget/telnet_log_line.html')

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


def unmatched_patterns_view(*args, **kwargs):
    """Initial view load - shows all existing patterns. Granular updates handled separately."""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_test = module.templates.get_template('telnet_log_widget/view_unmatched_patterns.html')
    template_view_menu = module.templates.get_template('telnet_log_widget/control_view_menu.html')
    template_pattern_table_header = module.templates.get_template('telnet_log_widget/unmatched_pattern_table_header.html')
    template_table_footer = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_footer.html')

def update_unmatched_patterns_selection_status(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    location_identifier = updated_values_dict["identifier"]

    # Sanitize dataset for HTML ID (replace spaces with underscores, lowercase)
    sanitized_dataset = module.dom_management.sanitize_for_html_id(updated_values_dict["dataset"])

    module.dom_management.update_selection_status(
        *args, **kwargs,
        target_module=module,
        dom_element_root=[location_identifier],
        dom_element_select_root=[location_identifier, "selected_by"],
        dom_action_active="deselect_dom_element",
        dom_action_inactive="select_dom_element",
        dom_element_id={
            "id": "location_table_row_{}_{}_{}_control_select_link".format(
                sanitized_dataset,
                updated_values_dict["owner"],
                updated_values_dict["identifier"]
            )
        }
    )

    update_unmatched_patterns_delete_button_status(module, *args, **kwargs)

def update_unmatched_patterns_delete_button_status(*args, **kwargs):
    module = args[0]

    module.dom_management.update_delete_button_status(
        *args, **kwargs,
        target_module=module,
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        dom_action="delete_selected_dom_elements",
        dom_element_id={
            "id": "manage_locations_control_action_delete_link"
        }
    )

def update_telnet_log(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    # Iterate directly over connected clients (no need to convert to list)
    for clientid in module.webserver.connected_clients.keys():
        current_view = module.get_current_view(clientid)
        if current_view == "frontend":
            telnet_log_line = module.templates.get_template('telnet_log_widget/telnet_log_line.html')
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
        "module_telnet/telnet_lines": update_telnet_log,

        "module_telnet/unmatched_patterns/%map_identifier%/%element_identifier%/selected_by":
            update_selection_status,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
