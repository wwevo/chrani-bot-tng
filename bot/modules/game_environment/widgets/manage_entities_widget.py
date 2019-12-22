from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_entity_table_row_css_class(entity_dict):
    css_classes = []
    return " ".join(css_classes)


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = module.get_current_view(dispatchers_steamid)

    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    elif current_view == "modal":
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)
        modal_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def modal_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    all_available_entity_dicts = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})
    all_selected_elements_count = 0
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    for map_identifier, entity_dicts in all_available_entity_dicts.items():
        if active_dataset == map_identifier:
            for entity_id, entity_dict in entity_dicts.items():
                entity_is_selected_by = entity_dict.get("selected_by", [])
                if dispatchers_steamid in entity_is_selected_by:
                    all_selected_elements_count += 1

    modal_confirm_delete = module.dom_management.get_delete_confirm_modal(
        module,
        count=all_selected_elements_count,
        target_module="module_game_environment",
        dom_element_id="entity_table_modal_action_delete_button",
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
            "id": "manage_entities_widget_modal",
            "type": "div",
            "selector": "body > main > div"
        }
    )


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_frontend = module.templates.get_template('manage_entities_widget/view_frontend.html')
    template_table_rows = module.templates.get_template('manage_entities_widget/table_row.html')
    template_table_header = module.templates.get_template('manage_entities_widget/table_header.html')
    template_table_footer = module.templates.get_template('manage_entities_widget/table_footer.html')

    template_options_toggle = module.templates.get_template('manage_entities_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('manage_entities_widget/control_switch_options_view.html')

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    all_available_entity_dicts = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})

    table_rows = ""
    all_selected_elements_count = 0
    for map_identifier, entity_dicts in all_available_entity_dicts.items():
        if active_dataset == map_identifier:
            for entity_id, entity_dict in entity_dicts.items():
                entity_is_selected_by = entity_dict.get("selected_by", [])

                entity_entry_selected = False
                if dispatchers_steamid in entity_is_selected_by:
                    entity_entry_selected = True
                    all_selected_elements_count += 1

                control_select_link = module.dom_management.get_selection_dom_element(
                    module,
                    target_module="module_game_environment",
                    dom_element_select_root=["selected_by"],
                    dom_element=entity_dict,
                    dom_element_entry_selected=entity_entry_selected,
                    dom_action_inactive="select_dom_element",
                    dom_action_active="deselect_dom_element"
                )

                table_rows += module.template_render_hook(
                    module,
                    template=template_table_rows,
                    entity=entity_dict,
                    css_class=get_entity_table_row_css_class(entity_dict),
                    control_select_link=control_select_link
                )

    current_view = module.get_current_view(dispatchers_steamid)

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

    dom_element_delete_button = module.dom_management.get_delete_button_dom_element(
        module,
        count=all_selected_elements_count,
        target_module="module_game_environment",
        dom_element_id="entity_table_widget_action_delete_button",
        dom_action="delete_selected_dom_elements",
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root
    )

    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        options_toggle=options_toggle,
        table_header=module.template_render_hook(
            module,
            template=template_table_header
        ),
        table_rows=table_rows,
        table_footer=module.template_render_hook(
            module,
            template=template_table_footer,
            action_delete_button=dom_element_delete_button
        )
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "manage_entities_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_frontend = module.templates.get_template('manage_entities_widget/view_options.html')
    template_options_toggle = module.templates.get_template('manage_entities_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('manage_entities_widget/control_switch_options_view.html')

    options_toggle = module.template_render_hook(
        module,
        template=template_options_toggle,
        control_switch_options_view=module.template_render_hook(
            module,
            template=template_options_toggle_view,
            options_view_toggle=False,
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
            "id": "manage_entities_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def table_rows(*args, ** kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    method = kwargs.get("method", None)
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)

    if method in ["upsert", "edit", "insert"]:
        for clientid in module.webserver.connected_clients.keys():
            current_view = (
                module.dom.data
                .get("module_game_environment", {})
                .get("visibility", {})
                .get(clientid, {})
                .get("current_view", "frontend")
            )
            if current_view == "frontend":
                template_table_rows = module.templates.get_template('manage_entities_widget/table_row.html')

                for entity_id, entity_dict in updated_values_dict.items():
                    try:
                        table_row_id = "entity_table_row_{}_{}".format(
                            str(entity_dict["dataset"]),
                            str(entity_id)
                        )
                    except KeyError:
                        table_row_id = "manage_entities_widget"

                    selected_entity_entries = (
                        module.dom.data
                        .get("module_game_environment", {})
                        .get("elements", {})
                        .get(active_dataset, {})
                        .get(entity_id, {})
                        .get("selected_by", [])
                    )

                    entity_entry_selected = False
                    if clientid in selected_entity_entries:
                        entity_entry_selected = True

                    control_select_link = module.dom_management.get_selection_dom_element(
                        module,
                        target_module="module_game_environment",
                        dom_element_select_root=["selected_by"],
                        dom_element=entity_dict,
                        dom_element_entry_selected=entity_entry_selected,
                        dom_action_inactive="select_dom_element",
                        dom_action_active="deselect_dom_element"
                    )

                    table_row = module.template_render_hook(
                        module,
                        template=template_table_rows,
                        entity=entity_dict,
                        css_class=get_entity_table_row_css_class(entity_dict),
                        control_select_link=control_select_link
                    )

                    module.webserver.send_data_to_client_hook(
                        module,
                        payload=table_row,
                        data_type="table_row",
                        clients=[clientid],
                        target_element={
                            "id": table_row_id,
                            "type": "tr",
                            "class": get_entity_table_row_css_class(entity_dict),
                            "selector": "body > main > div > div#manage_entities_widget > main > table > tbody"
                        }
                    )
    elif method == "remove":
        entity_origin = updated_values_dict[2]
        entity_id = updated_values_dict[3]
        module.webserver.send_data_to_client_hook(
            module,
            data_type="remove_table_row",
            clients="all",
            target_element={
                "id": "entity_table_row_{}_{}".format(
                    str(entity_origin),
                    str(entity_id)
                )
            }
        )

        update_delete_button_status(module, *args, **kwargs)


def update_widget(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    method = kwargs.get("method", None)
    if method in ["update"]:
        entity_dict = updated_values_dict
        player_clients_to_update = list(module.webserver.connected_clients.keys())

        for clientid in player_clients_to_update:
            try:
                current_view = (
                    module.dom.data
                    .get("module_game_environment", {})
                    .get("visibility", {})
                    .get(clientid, {})
                    .get("current_view", "frontend")
                )
                table_row_id = "entity_table_row_{}_{}".format(
                    str(entity_dict.get("dataset", None)),
                    str(entity_dict.get("id", None))

                )
                if current_view == "frontend":
                    module.webserver.send_data_to_client_hook(
                        module,
                        payload=entity_dict,
                        data_type="table_row_content",
                        clients="all",
                        method="update",
                        target_element={
                            "id": table_row_id,
                            "parent_id": "manage_entities_widget",
                            "module": "game_environment",
                            "type": "tr",
                            "selector": "body > main > div > div#manage_entities_widget",
                            "class": get_entity_table_row_css_class(entity_dict),
                        }
                    )
            except AttributeError as error:
                pass
            except KeyError as error:
                pass


def update_selection_status(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    module.dom_management.update_selection_status(
        *args, **kwargs,
        target_module=module,
        dom_action_active="deselect_dom_element",
        dom_action_inactive="select_dom_element",
        dom_element_id={
            "id": "entity_table_row_{}_{}_control_select_link".format(
                updated_values_dict["dataset"],
                updated_values_dict["identifier"]
            )
        }
    )

    update_delete_button_status(module, *args, **kwargs)


def update_delete_button_status(*args, **kwargs):
    module = args[0]

    module.dom_management.update_delete_button_status(
        *args, **kwargs,
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        target_module=module,
        dom_action="delete_selected_dom_elements",
        dom_element_id={
            "id": "entity_table_widget_action_delete_button"
        }
    )


widget_meta = {
    "description": "sends and updates a table of all currently known entities",
    "main_widget": select_view,
    "handlers": {
        "module_game_environment/visibility/%steamid%/current_view":
            select_view,
        "module_game_environment/elements/%map_identifier%/%id%":
            table_rows,
        "module_game_environment/elements/%map_identifier%/%id%/pos":
            update_widget,
        "module_game_environment/elements/%map_identifier%/%id%/selected_by":
            update_selection_status,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
