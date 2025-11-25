from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]

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
    elif current_view == "delete-modal":
        unmatched_patterns_view(module, dispatchers_steamid=dispatchers_steamid)
        delete_modal_view(module, dispatchers_steamid=dispatchers_steamid)
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
    from bot.logger import get_logger
    logger = get_logger("telnet_log_widget")

    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    # Load templates
    template_unmatched_patterns = module.templates.get_template('telnet_log_widget/view_unmatched_patterns.html')
    template_view_menu = module.templates.get_template('telnet_log_widget/control_view_menu.html')
    template_table_header = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_header.html')
    template_table_row = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_row.html')
    template_table_footer = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_footer.html')

    # Build table rows
    table_rows_list = []
    all_unmatched_patterns = module.dom.data.get("module_telnet", {}).get("elements", {})
    all_selected_elements_count = 0
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    # Iterate over map_identifier -> pattern_id -> pattern_data
    for map_identifier, patterns_dict in all_unmatched_patterns.items():

        if active_dataset == map_identifier:

            for pattern_id, pattern_data in patterns_dict.items():
                pattern_is_selected_by = pattern_data.get("selected_by", [])

                pattern_entry_selected = False
                if dispatchers_steamid in pattern_is_selected_by:
                    pattern_entry_selected = True
                    all_selected_elements_count += 1

                # Generate control_select_link FIRST with original pattern_data


                control_select_link = module.dom_management.get_selection_dom_element(
                    module,
                    target_module="module_telnet",
                    dom_element_select_root=["selected_by"],
                    dom_element=pattern_data,
                    dom_element_entry_selected=pattern_entry_selected,
                    dom_action_inactive="select_dom_element",
                    dom_action_active="deselect_dom_element"
                )


                # THEN create template dict with sanitized dataset
                pattern_dict_for_template = pattern_data.copy()
                pattern_dict_for_template["dataset"] = module.dom_management.sanitize_for_html_id(map_identifier)
                pattern_dict_for_template["dataset_original"] = map_identifier
                pattern_dict_for_template["name"] = pattern_data.get("pattern", "")
                pattern_dict_for_template["type"] = pattern_data.get("example_line", "")

                rendered_row = module.template_render_hook(
                    module,
                    template=template_table_row,
                    unmatched_pattern=pattern_dict_for_template,
                    control_select_link=control_select_link
                )

                table_rows_list.append(rendered_row)

    table_rows = ''.join(table_rows_list) if table_rows_list else '<tr><td colspan="3">No unmatched patterns yet...</td></tr>'



    # Render view menu
    current_view = module.get_current_view(dispatchers_steamid)
    options_toggle = module.template_render_hook(
        module,
        template=template_view_menu,
        views=VIEW_REGISTRY,
        current_view=current_view,
        steamid=dispatchers_steamid
    )

    # Render table header and footer
    table_header = module.template_render_hook(
        module,
        template=template_table_header
    )

    # Create delete button
    action_delete_button = module.dom_management.get_delete_button_dom_element(
        module,
        count=all_selected_elements_count,
        target_module="module_telnet",
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        dom_element_id="unmatched_patterns_table_widget_action_delete_button",
        dom_action="delete_selected_dom_elements"
    )

    table_footer = module.template_render_hook(
        module,
        template=template_table_footer,
        action_delete_button=action_delete_button
    )

    # Render final view
    data_to_emit = module.template_render_hook(
        module,
        template=template_unmatched_patterns,
        options_toggle=options_toggle,
        table_header=table_header,
        table_rows=table_rows,
        table_footer=table_footer
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




def delete_modal_view(*args, **kwargs):
    """Display delete confirmation modal for selected patterns."""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    # Count selected patterns for this user
    all_unmatched_patterns = module.dom.data.get("module_telnet", {}).get("elements", {})
    all_selected_elements_count = 0
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    for map_identifier, patterns_dict in all_unmatched_patterns.items():
        if active_dataset == map_identifier:
            for pattern_id, pattern_data in patterns_dict.items():
                pattern_is_selected_by = pattern_data.get("selected_by", [])
                if dispatchers_steamid in pattern_is_selected_by:
                    all_selected_elements_count += 1

    # Generate delete confirmation modal
    modal_confirm_delete = module.dom_management.get_delete_confirm_modal(
        module,
        count=all_selected_elements_count,
        target_module="module_telnet",
        dom_element_id="unmatched_patterns_table_modal_action_delete_button",
        dom_action="delete_selected_dom_elements",
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        confirmed="True"
    )

    data_to_emit = modal_confirm_delete

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="modal_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "unmatched_pattern_table_modal",
            "type": "div",
            "selector": "body > main > div#telnet_log_widget > main > div.dialog"
        }
    )


def add_or_update_pattern_row(*args, **kwargs):
    """Handler for new/updated patterns - adds row to table."""
    from bot.logger import get_logger
    logger = get_logger("telnet_log_widget")

    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    method = kwargs.get("method", None)
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)



    if method in ["upsert", "edit", "insert", "update"]:
        template_table_row = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_row.html')

        for clientid in module.webserver.connected_clients.keys():
            current_view = module.get_current_view(clientid)


            if current_view == "test":  # Note: using "test" view for patterns
                for pattern_id, pattern_data in updated_values_dict.items():


                    # Get selected_by from full DOM data
                    pattern_is_selected_by = (
                        module.dom.data
                        .get("module_telnet", {})
                        .get("elements", {})
                        .get(active_dataset, {})
                        .get(pattern_id, {})
                        .get("selected_by", [])
                    )

                    pattern_entry_selected = False
                    if clientid in pattern_is_selected_by:
                        pattern_entry_selected = True

                    # Generate control_select_link with original data
                    control_select_link = module.dom_management.get_selection_dom_element(
                        module,
                        target_module="module_telnet",
                        dom_element_select_root=["selected_by"],
                        dom_element=pattern_data,
                        dom_element_entry_selected=pattern_entry_selected,
                        dom_action_inactive="select_dom_element",
                        dom_action_active="deselect_dom_element"
                    )



                    # Prepare template dict with sanitized dataset
                    map_identifier = pattern_data.get("dataset", "unknown")
                    pattern_dict_for_template = pattern_data.copy()
                    pattern_dict_for_template["dataset"] = module.dom_management.sanitize_for_html_id(map_identifier)
                    pattern_dict_for_template["dataset_original"] = map_identifier
                    pattern_dict_for_template["name"] = pattern_data.get("pattern", "")
                    pattern_dict_for_template["type"] = pattern_data.get("example_line", "")



                    table_row = module.template_render_hook(
                        module,
                        template=template_table_row,
                        unmatched_pattern=pattern_dict_for_template,
                        control_select_link=control_select_link
                    )



                    sanitized_dataset = pattern_dict_for_template["dataset"]
                    table_row_id = "unmatched_pattern_table_row_{}_{}".format(
                        sanitized_dataset,
                        pattern_id
                    )



                    module.webserver.send_data_to_client_hook(
                        module,
                        payload=table_row,
                        data_type="table_row",
                        clients=[clientid],
                        target_element={
                            "id": table_row_id,
                            "type": "tr",
                            "selector": "body > main > div > div#telnet_log_widget > main > table > tbody#unmatched_pattern_table"
                        }
                    )


def update_unmatched_patterns_selection_status(*args, **kwargs):
    from bot.logger import get_logger
    logger = get_logger("telnet_log_widget")


    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    # Sanitize dataset for HTML ID (replace spaces with underscores, lowercase)
    sanitized_dataset = module.dom_management.sanitize_for_html_id(updated_values_dict["dataset"])

    module.dom_management.update_selection_status(
        *args, **kwargs,
        target_module=module,
        dom_action_active="deselect_dom_element",
        dom_action_inactive="select_dom_element",
        dom_element_id={
            "id": "unmatched_pattern_table_row_{}_{}_control_select_link".format(
                sanitized_dataset,
                updated_values_dict["identifier"]
            )
        }
    )

    # Update delete button count when selection changes
    update_delete_button_status(module, *args, **kwargs)


def update_delete_button_status(*args, **kwargs):
    """Update delete button status/count when selections change."""
    module = args[0]

    module.dom_management.update_delete_button_status(
        *args, **kwargs,
        target_module=module,
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        dom_action="delete_selected_dom_elements",
        dom_element_id={
            "id": "unmatched_patterns_control_action_delete_link"
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
        "module_telnet/elements/%map_identifier%/%element_identifier%":
            add_or_update_pattern_row,
        "module_telnet/elements/%map_identifier%/%element_identifier%/selected_by":
            update_unmatched_patterns_selection_status,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
