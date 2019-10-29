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


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    template_frontend = module.templates.get_template('locations_widget/view_frontend.html')

    template_options_toggle = module.templates.get_template('locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_create_new_view.html'
    )

    control_edit_link = module.dom_management.templates.get_template('control_edit_link.html')
    control_enabled_link = module.dom_management.templates.get_template('control_enabled_link.html')

    template_table_header = module.templates.get_template('locations_widget/table_header.html')
    template_table_rows = module.templates.get_template('locations_widget/table_row.html')
    template_table_footer = module.templates.get_template('locations_widget/table_footer.html')

    table_rows = ""
    all_available_locations = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})
    all_selected_elements_count = 0
    current_map_identifier = module.dom.data.get("module_environment", {}).get("gameprefs", {}).get("GameName", None)
    for map_identifier, location_owner in all_available_locations.items():
        if current_map_identifier == map_identifier:
            for player_steamid, player_locations in location_owner.items():
                player_dict = (
                    module.dom.data
                    .get("module_players", {})
                    .get("elements", {})
                    .get(current_map_identifier, {})
                    .get(player_steamid, {})
                )
                for identifier, location_dict in player_locations.items():
                    location_is_selected_by = (
                        module.dom.data
                        .get("module_dom", {})
                        .get("module_locations", {})
                        .get(current_map_identifier, {})
                        .get(player_steamid, {})
                        .get(identifier, {})
                        .get("selected_by", [])
                    )

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
                        dom_action_inactive="select_entry",
                        dom_action_active="deselect_entry"
                    )

                    table_rows += module.template_render_hook(
                        module,
                        template_table_rows,
                        location=location_dict,
                        player_dict=player_dict,
                        control_select_link=control_select_link,
                        control_enabled_link=module.template_render_hook(
                            module,
                            control_enabled_link,
                            location=location_dict,
                        ),
                        control_edit_link=module.template_render_hook(
                            module,
                            control_edit_link,
                            dispatchers_steamid=dispatchers_steamid,
                            location=location_dict,
                        )
                    )

    dom_element_delete_button = module.dom_management.get_delete_button_dom_element(
        module,
        count=all_selected_elements_count,
        target_module="module_locations",
        dom_element_id="manage_locations_control_action_delete_link",
        dom_action="delete_selected"
    )

    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
        options_toggle=module.template_render_hook(
            module,
            template_options_toggle,
            control_switch_options_view=module.template_render_hook(
                module,
                template_options_toggle_view,
                steamid=dispatchers_steamid,
                options_view_toggle=True
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=True
            )
        ),
        table_header=module.template_render_hook(
            module,
            template_table_header
        ),
        table_rows=table_rows,
        table_footer=module.template_render_hook(
            module,
            template_table_footer,
            action_delete_button=dom_element_delete_button
        )

    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    template_frontend = module.templates.get_template('locations_widget/view_options.html')
    template_options_toggle = module.templates.get_template('locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_create_new_view.html'
    )

    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
        options_toggle=module.template_render_hook(
            module,
            template_options_toggle,
            control_switch_options_view=module.template_render_hook(
                module,
                template_options_toggle_view,
                steamid=dispatchers_steamid,
                options_view_toggle=False,
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=True,
            )
        ),
        widget_options=module.options,
        available_actions=module.all_available_actions_dict,
        available_widgets=module.all_available_widgets_dict
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "locations_widget",
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

    template_frontend = module.templates.get_template('locations_widget/view_create_new.html')

    template_options_toggle = module.templates.get_template('locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_create_new_view.html'
    )

    control_player_location_view = module.templates.get_template(
        'locations_widget/control_player_location.html'
    )

    player_coordinates = module.dom.data.get("module_players", {}).get("players", {}).get(dispatchers_steamid, {}).get(
        "pos", {"x": 0, "y": 0, "z": 0}
    )

    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
        options_toggle=module.template_render_hook(
            module,
            template_options_toggle,
            control_switch_options_view=module.template_render_hook(
                module,
                template_options_toggle_view,
                steamid=dispatchers_steamid,
                options_view_toggle=True
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=False
            ),
            control_player_location_view=module.template_render_hook(
                module,
                control_player_location_view,
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
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def table_row(*args, **kwargs):
    module = args[0]
    method = kwargs.get("method", None)
    updated_values_dict = kwargs.get("updated_values_dict", None)
    original_values_dict = kwargs.get("original_values_dict", None)

    template_table_rows = module.templates.get_template('locations_widget/table_row.html')

    control_edit_link = module.dom_management.templates.get_template('control_edit_link.html')
    control_enabled_link = module.dom_management.templates.get_template('control_enabled_link.html')

    if updated_values_dict is not None:
        if method == "upsert" or method == "edit":
            current_map_identifier = (
                module.dom.data
                .get("module_environment", {})
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
                table_is_visible = True if any(visibility_conditions) else False
                if table_is_visible:  # only relevant if the table is shown
                    for player_steamid, locations in updated_values_dict.items():
                        player_dict = (
                            module.dom.data
                            .get("module_players", {})
                            .get("elements", {})
                            .get(current_map_identifier, {})
                            .get(player_steamid, {})
                        )
                        for identifier, location_dict in locations.items():
                            location_is_selected_by = (
                                module.dom.data
                                .get("module_dom", {})
                                .get("module_locations", {})
                                .get(current_map_identifier, {})
                                .get(player_steamid, {})
                                .get(identifier, {})
                                .get("selected_by", [])
                            )
                            location_entry_selected = False
                            if clientid in location_is_selected_by:
                                location_entry_selected = True

                            try:
                                table_row_id = "manage_locations_table_row_{}_{}_{}".format(
                                    str(updated_values_dict[player_steamid][identifier]["origin"]),
                                    str(player_steamid),
                                    str(identifier)
                                )
                            except KeyError:
                                table_row_id = "locations_widget"

                            control_select_link = module.dom_management.get_selection_dom_element(
                                module,
                                target_module="module_locations",
                                dom_element_select_root=[identifier, "selected_by"],
                                dom_element=location_dict,
                                dom_element_entry_selected=location_entry_selected,
                                dom_action_inactive="select_entry",
                                dom_action_active="deselect_entry"
                            )
                            rendered_table_row = module.template_render_hook(
                                module,
                                template_table_rows,
                                location=location_dict,
                                player_dict=player_dict,
                                control_select_link=control_select_link,
                                control_enabled_link=module.template_render_hook(
                                    module,
                                    control_enabled_link,
                                    location=location_dict,
                                ),
                                control_edit_link=module.template_render_hook(
                                    module,
                                    control_edit_link,
                                    location=location_dict,
                                ),
                                css_class=get_table_row_css_class(location_dict)
                            )

                            module.webserver.send_data_to_client_hook(
                                module,
                                event_data=rendered_table_row,
                                data_type="table_row",
                                clients=[clientid],
                                target_element={
                                    "id": table_row_id,
                                    "type": "tr",
                                    "class": get_table_row_css_class(location_dict),
                                    "selector": "body > main > div > div#locations_widget > main > table > tbody"
                                }
                            )
                else:  # table is not visible or current user, skip it!
                    continue
        if method == "remove":  # callback_dict sent us here with a removal notification!
            for steamid, identifier in updated_values_dict.items():
                try:
                    if identifier in original_values_dict[steamid]:
                        module.webserver.send_data_to_client_hook(
                            module,
                            data_type="remove_table_row",
                            clients="all",
                            target_element={
                                "id": "manage_locations_table_row_{}_{}_{}".format(
                                    str(original_values_dict[steamid][identifier]["origin"]),
                                    str(steamid),
                                    str(identifier)
                                ),
                            }
                        )

                except TypeError:
                    # we are not deleting, so we are skipping any actions
                    pass

            update_delete_button_status(module, *args, **kwargs)


def update_player_location(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    webserver_logged_in_users = module.dom.data.get("module_webserver", {}).get(
        "webserver_logged_in_users", {}
    ).keys()

    dispatchers_steamid = updated_values_dict.get("steamid")
    if dispatchers_steamid not in webserver_logged_in_users:
        return

    control_player_location_view = module.templates.get_template(
        'locations_widget/control_player_location.html'
    )

    player_coordinates = updated_values_dict.get("pos", {})

    data_to_emit = module.template_render_hook(
        module,
        control_player_location_view,
        pos_x=player_coordinates["x"],
        pos_y=player_coordinates["y"],
        pos_z=player_coordinates["z"]
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
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
        dom_action_active="deselect_entry",
        dom_action_inactive="select_entry",
        dom_element_id={
            "id": "manage_locations_table_row_{}_{}_{}_control_select_link".format(
                updated_values_dict["origin"],
                updated_values_dict["owner"],
                updated_values_dict["identifier"]
            )
        }
    )

    update_delete_button_status(module, *args, **kwargs)


def update_enabled_flag(*args, **kwargs):
    module = args[0]
    original_values_dict = kwargs.get("original_values_dict", None)

    control_enable_link = module.templates.get_template('locations_widget/control_enabled_link.html')

    location_origin = original_values_dict.get("origin", None)
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
        control_enable_link,
        location=location_dict,
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="element_content",
        clients="all",
        method="update",
        target_element={
            "id": "manage_locations_table_row_{}_{}_{}_control_enabled_link".format(
                location_origin,
                location_owner,
                location_identifier
            ),
        }
    )


def update_delete_button_status(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    location_identifier = updated_values_dict["identifier"]

    module.dom_management.update_delete_button_status(
        *args, **kwargs,
        target_module=module,
        dom_element_root=[location_identifier],
        dom_element_select_root=[location_identifier, "selected_by"],
        dom_action="delete_selected",
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
        "module_dom/module_locations/%map_identifier%/%steamid%/%element_identifier%/selected_by":
            update_selection_status,
        "module_locations/elements/%map_identifier%/%steamid%/%element_identifier%/is_enabled":
            update_enabled_flag,
        "module_players/elements/%map_identifier%/%steamid%/pos":
            update_player_location
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
