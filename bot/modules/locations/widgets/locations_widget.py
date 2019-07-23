from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(
        dispatchers_steamid, {}
    ).get(
        "current_view", "frontend"
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid)
    elif current_view == "create_new":
        create_new_view(module, dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid)


def frontend_view(module, dispatchers_steamid=None):
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

    selected_location_entries = module.dom.data.get("module_locations", {}).get("selected", {}).get(dispatchers_steamid, [])

    table_rows = ""
    player_locations = module.dom.data.get("module_locations", {}).get("locations", {}).get(dispatchers_steamid, {})
    for identifier, location_dict in player_locations.items():
        location_entry_selected = False
        if identifier in selected_location_entries:
            location_entry_selected = True

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
                count=len(selected_location_entries),
                delete_selected_entries_active=True if len(selected_location_entries) >= 1 else False
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


def options_view(module, dispatchers_steamid=None):
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


def create_new_view(module, dispatchers_steamid=None):
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


def update_component(*args, **kwargs):
    module = args[0]
    locations_identifier = kwargs.get("updated_values_dict").get("identifier", None)
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    control_select_link = module.templates.get_template('locations_widget/control_select_link.html')
    selected_locations_entries = kwargs.get("updated_values_dict").get(dispatchers_steamid, [])
    original_selected_locations_entries = kwargs.get("original_values_dict").get(dispatchers_steamid, [])
    template_action_delete_button = module.templates.get_template(
        'locations_widget/control_action_delete_button.html'
    )

    for identifier in original_selected_locations_entries + selected_locations_entries:
        location_entry_selected = True if identifier in selected_locations_entries else False
        data_to_emit = module.template_render_hook(
            module,
            control_select_link,
            location=module.dom.data.get("module_locations", {}).get("locations", {}).get(dispatchers_steamid, {}).get(
                identifier, None
            ),
            location_entry_selected=location_entry_selected
        )

        module.webserver.send_data_to_client_hook(
            module,
            event_data=data_to_emit,
            data_type="element_content",
            clients=[dispatchers_steamid],
            method="update",
            target_element={
                "id": "locations_table_row_{}_control_select_link".format(str(identifier)),
            }
        )

        data_to_emit = module.template_render_hook(
            module,
            template_action_delete_button,
            count=len(selected_locations_entries),
            delete_selected_entries_active=True if len(selected_locations_entries) >= 1 else False
        )

        module.webserver.send_data_to_client_hook(
            module,
            event_data=data_to_emit,
            data_type="element_content",
            clients=[dispatchers_steamid],
            method="replace",
            target_element={
                "id": "locations_widget_action_delete_button"
            }
        )


widget_meta = {
    "description": "shows locations and stuff",
    "main_widget": select_view,
    "handlers": {
        "module_locations/selected/%steamid%": update_component,
        "module_locations/visibility/%steamid%/current_view": select_view,
        "module_players/players/%steamid%/pos": update_player_location
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
