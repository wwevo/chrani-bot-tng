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
    from bot.logger import get_logger
    logger = get_logger("telnet_log_widget")

    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    logger.info(f"[DEBUG] unmatched_patterns_view called for steamid={dispatchers_steamid}")

    # Load templates
    template_unmatched_patterns = module.templates.get_template('telnet_log_widget/view_unmatched_patterns.html')
    template_view_menu = module.templates.get_template('telnet_log_widget/control_view_menu.html')
    template_table_header = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_header.html')
    template_table_row = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_row.html')
    template_table_footer = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_footer.html')

    # Build table rows
    table_rows_list = []
    all_unmatched_patterns = module.dom.data.get("module_telnet", {}).get("unmatched_patterns", {})
    all_selected_elements_count = 0
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    logger.info(f"[DEBUG] active_dataset={active_dataset}")
    logger.info(f"[DEBUG] all_unmatched_patterns keys={list(all_unmatched_patterns.keys())}")
    logger.info(f"[DEBUG] Total patterns in all maps: {sum(len(v) for v in all_unmatched_patterns.values())}")

    # Iterate over map_identifier -> pattern_id -> pattern_data
    for map_identifier, patterns_dict in all_unmatched_patterns.items():
        logger.info(f"[DEBUG] Checking map {map_identifier} (active={active_dataset}), has {len(patterns_dict)} patterns")
        if active_dataset == map_identifier:
            logger.info(f"[DEBUG] Map matches! Processing {len(patterns_dict)} patterns")
            for pattern_id, pattern_data in patterns_dict.items():
                logger.info(f"[DEBUG] Processing pattern {pattern_id}")
                logger.info(f"[DEBUG] pattern_data keys: {pattern_data.keys()}")

                pattern_is_selected_by = pattern_data.get("selected_by", [])

                pattern_entry_selected = False
                if dispatchers_steamid in pattern_is_selected_by:
                    pattern_entry_selected = True
                    all_selected_elements_count += 1

                # Generate control_select_link FIRST with original pattern_data
                logger.info(f"[DEBUG] Calling get_selection_dom_element for pattern {pattern_id}")
                logger.info(f"[DEBUG] pattern_data for control: owner={pattern_data.get('owner')}, identifier={pattern_data.get('identifier')}, dataset={pattern_data.get('dataset')}")
                control_select_link = module.dom_management.get_selection_dom_element(
                    module,
                    target_module="module_telnet",
                    dom_element_select_root=["selected_by"],
                    dom_element=pattern_data,
                    dom_element_entry_selected=pattern_entry_selected,
                    dom_action_inactive="select_dom_element",
                    dom_action_active="deselect_dom_element"
                )
                logger.info(f"[DEBUG] control_select_link HTML (first 200 chars): {control_select_link[:200] if control_select_link else 'NONE'}")

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
                logger.info(f"[DEBUG] Rendered row HTML (first 300 chars): {rendered_row[:300]}")
                table_rows_list.append(rendered_row)

    table_rows = ''.join(table_rows_list) if table_rows_list else '<tr><td colspan="3">No unmatched patterns yet...</td></tr>'

    logger.info(f"[DEBUG] Built {len(table_rows_list)} table rows, total HTML length: {len(table_rows)}")

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

    table_footer = module.template_render_hook(
        module,
        template=template_table_footer
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

    logger.info(f"[DEBUG] Final view HTML length: {len(data_to_emit)}, sending to client {dispatchers_steamid}")

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

    logger.info(f"[DEBUG] unmatched_patterns_view complete")

def add_or_update_pattern_row(*args, **kwargs):
    """Handler for new/updated patterns - adds row to table."""
    from bot.logger import get_logger
    logger = get_logger("telnet_log_widget")

    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    method = kwargs.get("method", None)
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    logger.info(f"[DEBUG] add_or_update_pattern_row called with method={method}, updated_values_dict keys={updated_values_dict.keys() if updated_values_dict else 'None'}")

    if method in ["upsert", "edit", "insert", "update"]:
        template_table_row = module.templates.get_template('telnet_log_widget/unmatched_patterns_table_row.html')

        for clientid in module.webserver.connected_clients.keys():
            current_view = module.get_current_view(clientid)
            logger.info(f"[DEBUG] Client {clientid} current_view: {current_view}")

            if current_view == "test":  # Note: using "test" view for patterns
                for pattern_id, pattern_data in updated_values_dict.items():
                    logger.info(f"[DEBUG] Processing pattern {pattern_id} for client {clientid}")

                    # Get selected_by from full DOM data
                    pattern_is_selected_by = (
                        module.dom.data
                        .get("module_telnet", {})
                        .get("unmatched_patterns", {})
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

                    logger.info(f"[DEBUG] control_select_link HTML: {control_select_link[:200] if control_select_link else 'NONE'}")

                    # Prepare template dict with sanitized dataset
                    map_identifier = pattern_data.get("dataset", "unknown")
                    pattern_dict_for_template = pattern_data.copy()
                    pattern_dict_for_template["dataset"] = module.dom_management.sanitize_for_html_id(map_identifier)
                    pattern_dict_for_template["dataset_original"] = map_identifier
                    pattern_dict_for_template["name"] = pattern_data.get("pattern", "")
                    pattern_dict_for_template["type"] = pattern_data.get("example_line", "")

                    logger.info(f"[DEBUG] pattern_dict_for_template: id={pattern_dict_for_template.get('id')}, dataset={pattern_dict_for_template.get('dataset')}, name length={len(pattern_dict_for_template.get('name', ''))}")

                    table_row = module.template_render_hook(
                        module,
                        template=template_table_row,
                        unmatched_pattern=pattern_dict_for_template,
                        control_select_link=control_select_link
                    )

                    logger.info(f"[DEBUG] table_row HTML (first 300 chars): {table_row[:300]}")

                    sanitized_dataset = pattern_dict_for_template["dataset"]
                    table_row_id = "unmatched_pattern_table_row_{}_{}".format(
                        sanitized_dataset,
                        pattern_id
                    )

                    logger.info(f"[DEBUG] Sending table_row to client {clientid}, row_id={table_row_id}")

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
    logger.info(f"[DEBUG] update_unmatched_patterns_selection_status called with kwargs={kwargs}")

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
        "module_telnet/unmatched_patterns/%map_identifier%/%element_identifier%":
            add_or_update_pattern_row,
        "module_telnet/unmatched_patterns/%map_identifier%/%element_identifier%/selected_by":
            update_unmatched_patterns_selection_status,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
