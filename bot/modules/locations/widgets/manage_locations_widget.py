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

    current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(
        dispatchers_steamid, {}
    ).get(
        "current_view", "frontend"
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    elif current_view == "create_new":
        create_new_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    template_frontend = module.templates.get_template('locations_widget/view_frontend.html')
    template_table_rows = module.templates.get_template('locations_widget/table_row.html')
    template_table_header = module.templates.get_template('locations_widget/table_header.html')

    template_options_toggle = module.templates.get_template('locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_create_new_view.html'
    )

    control_select_link = module.templates.get_template('locations_widget/control_select_link.html')
    template_action_delete_button = module.templates.get_template(
        'locations_widget/control_action_delete_button.html'
    )
    template_table_footer = module.templates.get_template('locations_widget/table_footer.html')

    table_rows = ""
    all_available_locations = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})
    all_selected_elements = 0
    for map_identifier, location_owner in all_available_locations.items():
        for owner_steamid, player_locations in location_owner.items():
            for identifier, location_dict in player_locations.items():
                location_entry_selected = False
                if dispatchers_steamid in location_dict.get("selected_by"):
                    location_entry_selected = True
                    all_selected_elements += 1

                table_rows += module.template_render_hook(
                    module,
                    template_table_rows,
                    location=location_dict,
                    steamid=dispatchers_steamid,
                    control_select_link=module.template_render_hook(
                        module,
                        control_select_link,
                        location_entry_selected=location_entry_selected,
                        location=location_dict,
                    )
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
            action_delete_button=module.template_render_hook(
                module,
                template_action_delete_button,
                count=all_selected_elements,
                delete_selected_entries_active=True if all_selected_elements >= 1 else False
            )
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


def create_new_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

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

    player_position = module.dom.data.get("module_players", {}).get("players", {}).get(dispatchers_steamid, {}).get(
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
                pos_x=player_position["x"],
                pos_y=player_position["y"],
                pos_z=player_position["z"]
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


def table_row(*args, **kwargs):
    module = args[0]
    method = kwargs.get("method", None)
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
    updated_values_dict = kwargs.get("updated_values_dict", None)
    original_values_dict = kwargs.get("original_values_dict", None)

    control_select_link = module.templates.get_template('locations_widget/control_select_link.html')
    template_table_rows = module.templates.get_template('locations_widget/table_row.html')

    if updated_values_dict is not None:
        if method == "upsert":  # callback_dict sent us here with an upsert notification!
            for clientid in module.webserver.connected_clients.keys():
                current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(clientid, {}).get(
                    "current_view", "frontend"
                )
                visibility_conditions = [
                    current_view == "frontend"
                ]
                table_is_visible = True if any(visibility_conditions) else False

                if table_is_visible:  # only relevant if the table is shown
                    for ownerid, locations in updated_values_dict.items():
                        for identifier, location_dict in locations.items():
                            rendered_table_row = module.template_render_hook(
                                module,
                                template_table_rows,
                                location=location_dict,
                                control_select_link=module.template_render_hook(
                                    module,
                                    control_select_link,
                                    location_entry_selected=False,
                                    location=location_dict,
                                ),
                                css_class=get_table_row_css_class(location_dict)
                            )

                            module.webserver.send_data_to_client_hook(
                                module,
                                event_data=rendered_table_row,
                                data_type="table_row",
                                clients=[clientid],
                                method="append",
                                target_element={
                                    "id": "manage_locations_widget",
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

            update_delete_button_status(module)


def update_player_location(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    dispatchers_steamid = updated_values_dict.get("steamid", None)
    webserver_logged_in_users = module.dom.data.get("module_webserver", {}).get(
        "webserver_logged_in_users", {}
    ).keys()
    if dispatchers_steamid not in webserver_logged_in_users:
        return

    player_position = updated_values_dict.get("pos", {})
    control_player_location_view = module.templates.get_template(
        'locations_widget/control_player_location.html'
    )
    data_to_emit = module.template_render_hook(
        module,
        control_player_location_view,
        pos_x=player_position["x"],
        pos_y=player_position["y"],
        pos_z=player_position["z"]
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
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
    original_values_dict = kwargs.get("original_values_dict", None)

    control_select_link = module.templates.get_template('locations_widget/control_select_link.html')

    location_origin = original_values_dict["origin"]
    location_owner = original_values_dict["owner"]
    location_identifier = original_values_dict["identifier"]

    location_dict = (
        module.dom.data.get("module_locations", {})
        .get("elements", {})
        .get(location_origin, {})
        .get(location_owner, {})
        .get(location_identifier, None)
    )

    location_entry_selected = False
    if dispatchers_steamid in location_dict.get("selected_by"):
        location_entry_selected = True

    data_to_emit = module.template_render_hook(
        module,
        control_select_link,
        location=location_dict,
        location_entry_selected=location_entry_selected
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="element_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "manage_locations_table_row_{}_{}_{}_control_select_link".format(
                location_origin,
                location_owner,
                location_identifier
            ),
        }
    )

    update_delete_button_status(module)


def update_delete_button_status(module):
    template_action_delete_button = module.templates.get_template('locations_widget/control_action_delete_button.html')

    for clientid in module.webserver.connected_clients.keys():
        all_available_elements = module.dom.data.get("module_locations", {}).get("elements", {})
        all_selected_elements = 0
        for map_identifier, location_owner in all_available_elements.items():
            for owner_steamid, player_locations in location_owner.items():
                for identifier, location_dict in player_locations.items():
                    if clientid in location_dict.get("selected_by"):
                        all_selected_elements += 1

        data_to_emit = module.template_render_hook(
            module,
            template_action_delete_button,
            count=all_selected_elements,
            delete_selected_entries_active=True if all_selected_elements >= 1 else False
        )

        module.webserver.send_data_to_client_hook(
            module,
            event_data=data_to_emit,
            data_type="element_content",
            clients=[clientid],
            method="replace",
            target_element={
                "id": "locations_widget_action_delete_button"
            }
        )


widget_meta = {
    "description": "shows locations and stuff",
    "main_widget": select_view,
    "component_widget": table_row,
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
        "module_players/players/%steamid%/pos":
            update_player_location
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
