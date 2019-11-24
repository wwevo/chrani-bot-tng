from bot import loaded_modules_dict
from os import path, pardir
from collections import OrderedDict

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_player_table_row_css_class(player_dict):
    css_classes = []

    if player_dict.get("is_online", False):
        css_classes.append("is_online")
    if player_dict.get("in_limbo", False):
        css_classes.append("in_limbo")
    if player_dict.get("is_initialized", False):
        css_classes.append("is_initialized")

    return " ".join(css_classes)


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = (
        module.dom.data
        .get("module_players", {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view", "frontend")
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    elif current_view == "info":
        show_info_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_frontend = module.templates.get_template('player_table_widget/view_frontend.html')
    template_table_rows = module.templates.get_template('player_table_widget/table_row.html')
    template_table_header = module.templates.get_template('player_table_widget/table_header.html')
    template_table_footer = module.templates.get_template('player_table_widget/table_footer.html')

    control_info_link = module.templates.get_template('player_table_widget/control_info_link.html')
    control_kick_link = module.templates.get_template('player_table_widget/control_kick_link.html')

    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('player_table_widget/control_switch_options_view.html')

    current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)

    all_available_player_dicts = module.dom.data.get(module.get_module_identifier(), {}).get("elements", {})

    table_rows = ""
    all_selected_elements_count = 0
    for map_identifier, player_dicts in all_available_player_dicts.items():
        if current_map_identifier == map_identifier:
            # have the online players displayed first initially!
            ordered_player_dicts = OrderedDict(sorted(player_dicts.items(), key=lambda x: x[1]['is_initialized'], reverse=True))
            for player_steamid, player_dict in ordered_player_dicts.items():
                if player_steamid == 'last_updated_servertime':
                    continue

                player_is_selected_by = player_dict.get("selected_by", [])

                player_entry_selected = False
                if dispatchers_steamid in player_is_selected_by:
                    player_entry_selected = True
                    all_selected_elements_count += 1

                control_select_link = module.dom_management.get_selection_dom_element(
                    module,
                    target_module="module_players",
                    dom_element_select_root=["selected_by"],
                    dom_element=player_dict,
                    dom_element_entry_selected=player_entry_selected,
                    dom_action_inactive="select_dom_element",
                    dom_action_active="deselect_dom_element"
                )

                table_rows += module.template_render_hook(
                    module,
                    template_table_rows,
                    player=player_dict,
                    css_class=get_player_table_row_css_class(player_dict),
                    control_info_link=module.template_render_hook(
                        module,
                        control_info_link,
                        player=player_dict
                    ),
                    control_kick_link=module.template_render_hook(
                        module,
                        control_kick_link,
                        player=player_dict,
                    ),
                    control_select_link=control_select_link
                )

    current_view = (
        module.dom.data
        .get("module_players", {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view", "frontend")
    )

    options_toggle = module.template_render_hook(
        module,
        template_options_toggle,
        control_switch_options_view=module.template_render_hook(
            module,
            template_options_toggle_view,
            options_view_toggle=(True if current_view == "frontend" else False),
            steamid=dispatchers_steamid
        )
    )

    dom_element_delete_button = module.dom_management.get_delete_button_dom_element(
        module,
        count=all_selected_elements_count,
        target_module="module_players",
        dom_element_id="player_table_widget_action_delete_button",
        dom_action="delete_selected_dom_elements",
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root
    )

    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
        options_toggle=options_toggle,
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
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "player_table_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_frontend = module.templates.get_template('player_table_widget/view_options.html')
    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('player_table_widget/control_switch_options_view.html')

    current_view = (
        module.dom.data
        .get("module_players", {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view", "frontend")
    )

    options_toggle = module.template_render_hook(
        module,
        template_options_toggle,
        control_switch_options_view=module.template_render_hook(
            module,
            template_options_toggle_view,
            options_view_toggle=(True if current_view == "frontend" else False),
            steamid=dispatchers_steamid
        )
    )

    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
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
            "id": "player_table_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def show_info_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_frontend = module.templates.get_template('player_table_widget/view_info.html')
    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('player_table_widget/control_switch_options_view.html')

    current_view = (
        module.dom.data
        .get("module_players", {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view", "frontend")
    )

    current_view_steamid = (
        module.dom.data
        .get("module_players", {})
        .get("visibility", {})
        .get(dispatchers_steamid, {})
        .get("current_view_steamid", "frontend")
    )

    options_toggle = module.template_render_hook(
        module,
        template_options_toggle,
        control_switch_options_view=module.template_render_hook(
            module,
            template_options_toggle_view,
            options_view_toggle=(True if current_view == "frontend" else False),
            steamid=dispatchers_steamid
        )
    )

    current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)
    player_dict = (
        module.dom.data
        .get("module_players", {})
        .get("elements", {})
        .get(current_map_identifier, {})
        .get(current_view_steamid, None)
    )

    data_to_emit = module.template_render_hook(
        module,
        template_frontend,
        options_toggle=options_toggle,
        player=player_dict
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "player_table_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def table_rows(*args, ** kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    method = kwargs.get("method", None)
    current_map_identifier = module.dom.data.get("module_environment", {}).get("current_game_name", None)

    if method in ["upsert", "edit", "insert"]:
        for clientid in module.webserver.connected_clients.keys():
            current_view = (
                module.dom.data
                .get("module_players", {})
                .get("visibility", {})
                .get(clientid, {})
                .get("current_view", "frontend")
            )
            if current_view == "frontend":
                template_table_rows = module.templates.get_template('player_table_widget/table_row.html')
                control_info_link = module.templates.get_template('player_table_widget/control_info_link.html')
                control_kick_link = module.templates.get_template('player_table_widget/control_kick_link.html')

                for player_steamid, player_dict in updated_values_dict.items():
                    try:
                        table_row_id = "player_table_row_{}_{}".format(
                            str(player_dict["dataset"]),
                            str(player_steamid)
                        )
                    except KeyError:
                        table_row_id = "player_table_widget"

                    selected_player_entries = (
                        module.dom.data
                        .get("module_players", {})
                        .get("elements", {})
                        .get(current_map_identifier, {})
                        .get(player_steamid, {})
                        .get("selected_by", [])
                    )

                    player_entry_selected = False
                    if clientid in selected_player_entries:
                        player_entry_selected = True

                    control_select_link = module.dom_management.get_selection_dom_element(
                        module,
                        target_module="module_players",
                        dom_element_select_root=["selected_by"],
                        dom_element=player_dict,
                        dom_element_entry_selected=player_entry_selected,
                        dom_action_inactive="select_dom_element",
                        dom_action_active="deselect_dom_element"
                    )

                    table_row = module.template_render_hook(
                        module,
                        template_table_rows,
                        player=player_dict,
                        css_class=get_player_table_row_css_class(player_dict),
                        control_info_link=module.template_render_hook(
                            module,
                            control_info_link,
                            player=player_dict
                        ),
                        control_kick_link=module.template_render_hook(
                            module,
                            control_kick_link,
                            player=player_dict,
                        ),
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
                            "class": get_player_table_row_css_class(player_dict),
                            "selector": "body > main > div > div#player_table_widget > main > table > tbody"
                        }
                    )
    elif method == "remove":
        player_origin = updated_values_dict[2]
        player_steamid = updated_values_dict[3]
        module.webserver.send_data_to_client_hook(
            module,
            data_type="remove_table_row",
            clients="all",
            target_element={
                "id": "player_table_row_{}_{}".format(
                    str(player_origin),
                    str(player_steamid)
                )
            }
        )

        update_delete_button_status(module, *args, **kwargs)


def update_widget(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    method = kwargs.get("method", None)
    if method in ["update"]:
        player_dict = updated_values_dict
        player_clients_to_update = list(module.webserver.connected_clients.keys())

        for clientid in player_clients_to_update:
            try:
                module_players = module.dom.data.get("module_players", {})
                current_view = (
                    module_players
                    .get("visibility", {})
                    .get(clientid, {})
                    .get("current_view", None)
                )
                table_row_id = "player_table_row_{}_{}".format(
                    str(player_dict.get("dataset", None)),
                    str(player_dict.get("steamid", None))

                )
                if current_view == "frontend":
                    module.webserver.send_data_to_client_hook(
                        module,
                        payload=player_dict,
                        data_type="table_row_content",
                        clients="all",
                        method="update",
                        target_element={
                            "id": table_row_id,
                            "parent_id": "player_table_widget",
                            "module": "players",
                            "type": "tr",
                            "selector": "body > main > div > div#player_table_widget",
                            "class": get_player_table_row_css_class(player_dict),
                        }
                    )
                elif current_view == "info":
                    module.webserver.send_data_to_client_hook(
                        module,
                        payload=player_dict,
                        data_type="table_row_content",
                        clients=[clientid],
                        method="update",
                        target_element={
                            "id": table_row_id,
                            "parent_id": "player_table_widget",
                            "module": "players",
                            "type": "tr",
                            "selector": "body > main > div > div#player_table_widget",
                            "class": get_player_table_row_css_class(player_dict),
                        }
                    )
            except AttributeError as error:
                # probably dealing with a player_dict here, not the players dict
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
            "id": "player_table_row_{}_{}_control_select_link".format(
                updated_values_dict["dataset"],
                updated_values_dict["owner"]
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
            "id": "player_table_widget_action_delete_button"
        }
    )


widget_meta = {
    "description": "sends and updates a table of all currently known players",
    "main_widget": select_view,
    "handlers": {
        # the %abc% placeholders can contain any text at all, it has no effect on anything but code-readability
        # the third line could just as well read
        #     "module_players/elements/%x%/%x%/%x%/selected_by": update_selection_status
        # and would still function the same as
        #     "module_players/elements/%map_identifier%/%steamid%/%element_identifier%/selected_by":
        #         update_selection_status
        "module_players/visibility/%steamid%/current_view":
            select_view,
        "module_players/elements/%map_identifier%/%steamid%":
            table_rows,
        "module_players/elements/%map_identifier%/%steamid%/pos":
            update_widget,
        "module_players/elements/%map_identifier%/%steamid%/selected_by":
            update_selection_status,
        # "module_players/elements/%map_identifier%/%steamid%/%element_identifier%/is_enabled":
        #     update_enabled_flag,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
