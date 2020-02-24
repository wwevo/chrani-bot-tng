from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_table_row_css_class(location_dict):
    is_enabled = location_dict.get("is_enabled", False)

    if is_enabled:
        css_class = "is_enabled"
    else:
        css_class = ""

    return css_class


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = (
        module.dom.data
        .get(module.get_module_identifier(), {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view", "frontend")
    )

    if current_view == "options":
        options_view(
            module,
            dispatchers_steamid=dispatchers_steamid,
            current_view=current_view
        )
    elif current_view == "special_locations":
        frontend_view(
            module,
            dispatchers_steamid=dispatchers_steamid,
            current_view=current_view
        )
    elif current_view == "modal":
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)
        modal_view(module, dispatchers_steamid=dispatchers_steamid)
    elif current_view == "create_new":
        edit_view(
            module,
            dispatchers_steamid=dispatchers_steamid,
            current_view=current_view
        )
    elif current_view == "edit_location_entry":
        location_owner = (
            module.dom.data
            .get(module.get_module_identifier(), {})
            .get("visibility", {})
            .get(dispatchers_steamid, {})
            .get("location_owner", None)
        )
        location_identifier = (
            module.dom.data
            .get(module.get_module_identifier(), {})
            .get("visibility", {})
            .get(dispatchers_steamid, {})
            .get("location_identifier", None)
        )
        location_origin = (
            module.dom.data
            .get(module.get_module_identifier(), {})
            .get("visibility", {})
            .get(dispatchers_steamid, {})
            .get("location_origin", None)
        )

        edit_view(
            module,
            dispatchers_steamid=dispatchers_steamid,
            location_owner=location_owner,
            location_identifier=location_identifier,
            location_origin=location_origin,
            current_view=current_view
        )
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def modal_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    all_available_locations = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})
    all_selected_elements_count = 0
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    for map_identifier, location_owner in all_available_locations.items():
        if active_dataset == map_identifier:
            for player_steamid, player_locations in location_owner.items():
                for identifier, location_dict in player_locations.items():
                    location_is_selected_by = location_dict.get("selected_by", [])
                    if dispatchers_steamid in location_is_selected_by:
                        all_selected_elements_count += 1

    modal_confirm_delete = module.dom_management.get_delete_confirm_modal(
        module,
        count=all_selected_elements_count,
        target_module="module_locations",
        dom_element_id="location_table_modal_action_delete_button",
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
            "id": "manage_locations_widget_modal",
            "type": "div",
            "selector": "body > main > div"
        }
    )


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
    current_view = kwargs.get("current_view", None)

    template_frontend = module.templates.get_template('manage_locations_widget/view_frontend.html')

    template_options_toggle = module.templates.get_template('manage_locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_create_new_view.html'
    )

    template_special_locations_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_special_locations_view.html'
    )

    control_player_location_view = module.templates.get_template(
        'manage_locations_widget/control_player_location.html'
    )

    player_coordinates = module.dom.data.get("module_players", {}).get("players", {}).get(dispatchers_steamid, {}).get(
        "pos", {"x": 0, "y": 0, "z": 0}
    )

    control_edit_link = module.templates.get_template('manage_locations_widget/control_edit_link.html')
    control_enabled_link = module.templates.get_template('manage_locations_widget/control_enabled_link.html')

    template_table_header = module.templates.get_template('manage_locations_widget/table_header.html')
    template_table_rows = module.templates.get_template('manage_locations_widget/table_row.html')
    template_table_footer = module.templates.get_template('manage_locations_widget/table_footer.html')

    table_rows = ""
    all_available_locations = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})
    all_selected_elements_count = 0
    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset", None)
    for map_identifier, location_owner in all_available_locations.items():
        if active_dataset == map_identifier:
            for player_steamid, player_locations in location_owner.items():
                player_dict = (
                    module.dom.data
                    .get("module_players", {})
                    .get("elements", {})
                    .get(active_dataset, {})
                    .get(player_steamid, {})
                )
                for identifier, location_dict in player_locations.items():
                    location_has_special_properties = True if len(location_dict.get("type", [])) >= 1 else False
                    if not location_has_special_properties and current_view == "special_locations":
                        continue

                    location_is_selected_by = location_dict.get("selected_by", [])

                    location_entry_selected = False
                    if dispatchers_steamid in location_is_selected_by:
                        location_entry_selected = True
                        all_selected_elements_count += 1

                    control_select_link = module.dom_management.get_selection_dom_element(
                        module,
                        target_module="module_locations",
                        dom_element_select_root=[identifier, "selected_by"],
                        dom_element=location_dict,
                        dom_element_entry_selected=location_entry_selected,
                        dom_action_inactive="select_dom_element",
                        dom_action_active="deselect_dom_element"
                    )

                    table_rows += module.template_render_hook(
                        module,
                        template=template_table_rows,
                        location=location_dict,
                        player_dict=player_dict,
                        control_select_link=control_select_link,
                        control_enabled_link=module.template_render_hook(
                            module,
                            template=control_enabled_link,
                            location=location_dict,
                        ),
                        control_edit_link=module.template_render_hook(
                            module,
                            template=control_edit_link,
                            dispatchers_steamid=dispatchers_steamid,
                            location=location_dict,
                        )
                    )

    dom_element_delete_button = module.dom_management.get_delete_button_dom_element(
        module,
        count=all_selected_elements_count,
        target_module="module_locations",
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        dom_element_id="manage_locations_control_action_delete_link",
        dom_action="delete_selected_dom_elements"
    )

    current_view = module.get_current_view(dispatchers_steamid)

    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        options_toggle=module.template_render_hook(
            module,
            template=template_options_toggle,
            control_switch_options_view=module.template_render_hook(
                module,
                template=template_options_toggle_view,
                steamid=dispatchers_steamid,
                options_view_toggle=(True if current_view in ["frontend", "special_locations"] else False)
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template=template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=True
            ),
            control_switch_special_locations_view=module.template_render_hook(
                module,
                template=template_special_locations_toggle_view,
                steamid=dispatchers_steamid,
                special_locations_view_toggle=(True if current_view in ["frontend"] else False)
            ),
            control_player_location_view=module.template_render_hook(
                module,
                template=control_player_location_view,
                pos_x=player_coordinates["x"],
                pos_y=player_coordinates["y"],
                pos_z=player_coordinates["z"]
            )
        ),
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
        target_element={
            "id": "manage_locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    template_frontend = module.templates.get_template('manage_locations_widget/view_options.html')
    template_options_toggle = module.templates.get_template('manage_locations_widget/control_switch_view.html')
    template_special_locations_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_special_locations_view.html'
    )

    template_options_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_create_new_view.html'
    )

    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        options_toggle=module.template_render_hook(
            module,
            template=template_options_toggle,
            control_switch_options_view=module.template_render_hook(
                module,
                template=template_options_toggle_view,
                steamid=dispatchers_steamid,
                options_view_toggle=False,
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template=template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=True,
            ),
            control_switch_special_locations_view=module.template_render_hook(
                module,
                template=template_special_locations_toggle_view,
                steamid=dispatchers_steamid,
                special_locations_view_toggle=True
            )
        ),
        widget_options=module.options,
        available_actions=module.available_actions_dict,
        available_triggers=module.available_triggers_dict,
        available_widgets=module.available_widgets_dict
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "manage_locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def special_locations_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    template_frontend = module.templates.get_template('manage_locations_widget/view_special_locations.html')
    template_special_locations_toggle = module.templates.get_template('manage_locations_widget/control_switch_view.html')
    template_special_locations_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_special_locations_view.html'
    )

    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        options_toggle=module.template_render_hook(
            module,
            template=template_special_locations_toggle,
            control_switch_options_view=module.template_render_hook(
                module,
                template=template_special_locations_toggle_view,
                steamid=dispatchers_steamid,
                options_view_toggle=False,
            )
        )
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "manage_locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def edit_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
    edit_mode = kwargs.get("current_view", None)

    location_to_edit_dict = {}
    if edit_mode == "edit_location_entry":
        location_owner = kwargs.get("location_owner", None)
        location_identifier = kwargs.get("location_identifier", None)
        location_origin = kwargs.get("location_origin", None)
        if all([
            location_owner is not None,
            location_identifier is not None,
            location_origin is not None
        ]):
            location_to_edit_dict = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {}).get(location_origin).get(location_owner).get(location_identifier)

    template_frontend = module.templates.get_template('manage_locations_widget/view_create_new.html')

    template_options_toggle = module.templates.get_template('manage_locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_create_new_view.html'
    )

    template_special_locations_toggle_view = module.templates.get_template(
        'manage_locations_widget/control_switch_special_locations_view.html'
    )

    control_player_location_view = module.templates.get_template(
        'manage_locations_widget/control_player_location.html'
    )

    player_coordinates = module.dom.data.get("module_players", {}).get("players", {}).get(dispatchers_steamid, {}).get(
        "pos", {"x": 0, "y": 0, "z": 0}
    )

    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        options_toggle=module.template_render_hook(
            module,
            template=template_options_toggle,
            control_switch_options_view=module.template_render_hook(
                module,
                template=template_options_toggle_view,
                steamid=dispatchers_steamid,
                options_view_toggle=True
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template=template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=False
            ),
            control_switch_special_locations_view=module.template_render_hook(
                module,
                template=template_special_locations_toggle_view,
                steamid=dispatchers_steamid,
                special_locations_view_toggle=True
            ),
            control_player_location_view=module.template_render_hook(
                module,
                template=control_player_location_view,
                pos_x=player_coordinates["x"],
                pos_y=player_coordinates["y"],
                pos_z=player_coordinates["z"]
            )
        ),
        widget_options=module.options,
        location_to_edit_dict=location_to_edit_dict
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "manage_locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def table_row(*args, **kwargs):
    module = args[0]
    method = kwargs.get("method", None)
    updated_values_dict = kwargs.get("updated_values_dict", None)
    original_values_dict = kwargs.get("original_values_dict", None)

    template_table_rows = module.templates.get_template('manage_locations_widget/table_row.html')

    control_edit_link = module.templates.get_template('manage_locations_widget/control_edit_link.html')
    control_enabled_link = module.templates.get_template('manage_locations_widget/control_enabled_link.html')

    if updated_values_dict is not None:
        if method == "upsert" or method == "edit":
            active_dataset = (
                module.dom.data
                .get("module_game_environment", {})
                .get("gameprefs", {})
                .get("GameName", None)
            )
            for clientid in module.webserver.connected_clients.keys():
                current_view = (
                    module.dom.data
                    .get(module.get_module_identifier(), {})
                    .get("visibility", {})
                    .get(clientid, {})
                    .get("current_view", "frontend")
                )
                visibility_conditions = [
                    current_view == "frontend"
                ]
                if any(visibility_conditions):  # only relevant if the table is shown
                    for player_steamid, locations in updated_values_dict.items():
                        player_dict = (
                            module.dom.data
                            .get("module_players", {})
                            .get("elements", {})
                            .get(active_dataset, {})
                            .get(player_steamid, {})
                        )
                        for identifier, location_dict in locations.items():
                            location_is_selected_by = location_dict.get("selected_by", [])

                            location_entry_selected = False
                            if clientid in location_is_selected_by:
                                location_entry_selected = True

                            try:
                                table_row_id = "location_table_row_{}_{}_{}".format(
                                    str(updated_values_dict[player_steamid][identifier]["dataset"]),
                                    str(player_steamid),
                                    str(identifier)
                                )
                            except KeyError:
                                table_row_id = "manage_locations_widget"

                            control_select_link = module.dom_management.get_selection_dom_element(
                                module,
                                target_module="module_locations",
                                dom_element_select_root=[identifier, "selected_by"],
                                dom_element=location_dict,
                                dom_element_entry_selected=location_entry_selected,
                                dom_action_inactive="select_dom_element",
                                dom_action_active="deselect_dom_element"
                            )
                            rendered_table_row = module.template_render_hook(
                                module,
                                template=template_table_rows,
                                location=location_dict,
                                player_dict=player_dict,
                                control_select_link=control_select_link,
                                control_enabled_link=module.template_render_hook(
                                    module,
                                    template=control_enabled_link,
                                    location=location_dict,
                                ),
                                control_edit_link=module.template_render_hook(
                                    module,
                                    template=control_edit_link,
                                    location=location_dict,
                                ),
                                css_class=get_table_row_css_class(location_dict)
                            )

                            module.webserver.send_data_to_client_hook(
                                module,
                                payload=rendered_table_row,
                                data_type="table_row",
                                clients=[clientid],
                                target_element={
                                    "id": table_row_id,
                                    "type": "tr",
                                    "class": get_table_row_css_class(location_dict),
                                    "selector": "body > main > div > div#manage_locations_widget > main > table > tbody"
                                }
                            )
                else:  # table is not visible or current user, skip it!
                    continue
        elif method == "remove":  # callback_dict sent us here with a removal notification!
            location_origin = updated_values_dict[2]
            player_steamid = updated_values_dict[3]
            location_identifier = updated_values_dict[-1]

            module.webserver.send_data_to_client_hook(
                module,
                data_type="remove_table_row",
                clients="all",
                target_element={
                    "id": "location_table_row_{}_{}_{}".format(
                        str(location_origin),
                        str(player_steamid),
                        str(location_identifier)
                    ),
                }
            )

            update_delete_button_status(module, *args, **kwargs)


def update_player_location(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    webserver_logged_in_users = module.dom.data.get("module_webserver", {}).get(
        "webserver_logged_in_users", []
    )

    dispatchers_steamid = updated_values_dict.get("steamid")
    if dispatchers_steamid not in webserver_logged_in_users:
        return

    control_player_location_view = module.templates.get_template(
        'manage_locations_widget/control_player_location.html'
    )

    player_coordinates = updated_values_dict.get("pos", {})

    data_to_emit = module.template_render_hook(
        module,
        template=control_player_location_view,
        pos_x=player_coordinates["x"],
        pos_y=player_coordinates["y"],
        pos_z=player_coordinates["z"]
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="element_content",
        method="replace",
        clients=dispatchers_steamid,
        target_element={
            "id": "current_player_pos"
        }
    )


def update_selection_status(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    location_identifier = updated_values_dict["identifier"]

    module.dom_management.update_selection_status(
        *args, **kwargs,
        target_module=module,
        dom_element_root=[location_identifier],
        dom_element_select_root=[location_identifier, "selected_by"],
        dom_action_active="deselect_dom_element",
        dom_action_inactive="select_dom_element",
        dom_element_id={
            "id": "location_table_row_{}_{}_{}_control_select_link".format(
                updated_values_dict["dataset"],
                updated_values_dict["owner"],
                updated_values_dict["identifier"]
            )
        }
    )

    update_delete_button_status(module, *args, **kwargs)


def update_enabled_flag(*args, **kwargs):
    module = args[0]
    original_values_dict = kwargs.get("original_values_dict", None)

    control_enable_link = module.templates.get_template('manage_locations_widget/control_enabled_link.html')

    location_origin = original_values_dict.get("dataset", None)
    location_owner = original_values_dict.get("owner", None)
    location_identifier = original_values_dict.get("identifier", None)

    location_dict = (
        module.dom.data.get("module_locations", {})
        .get("elements", {})
        .get(location_origin, {})
        .get(location_owner, {})
        .get(location_identifier, None)
    )

    data_to_emit = module.template_render_hook(
        module,
        template=control_enable_link,
        location=location_dict,
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="element_content",
        clients="all",
        method="update",
        target_element={
            "id": "location_table_row_{}_{}_{}_control_enabled_link".format(
                location_origin,
                location_owner,
                location_identifier
            ),
        }
    )


def update_delete_button_status(*args, **kwargs):
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


widget_meta = {
    "description": "shows locations and stuff",
    "main_widget": select_view,
    "handlers": {
        # the %abc% placeholders can contain any text at all, it has no effect on anything but code-readability
        # the third line could just as well read
        #     "module_locations/elements/%x%/%x%/%x%/selected_by": update_selection_status
        # and would still function the same as
        #     "module_locations/elements/%map_identifier%/%steamid%/%element_identifier%/selected_by":
        #         update_selection_status
        "module_locations/visibility/%steamid%/current_view":
            select_view,
        "module_locations/elements/%map_identifier%/%steamid%":
            table_row,
        "module_locations/elements/%map_identifier%/%steamid%/%element_identifier%/selected_by":
            update_selection_status,
        "module_locations/elements/%map_identifier%/%steamid%/%element_identifier%/is_enabled":
            update_enabled_flag,
        "module_players/elements/%map_identifier%/%steamid%/pos":
            update_player_location
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
