from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_player_table_row_css_class(player_dict):
    in_limbo = player_dict.get("in_limbo", False)
    is_online = player_dict.get("is_online", False)
    is_initialized = player_dict.get("is_initialized", False)

    css_class = ""

    # offline
    if not is_online and not in_limbo and not is_initialized:
        css_class = ""
    # offline + dead
    if not is_online and in_limbo and not is_initialized:
        css_class = "in_limbo"
    # online + logging in
    if is_online and in_limbo and not is_initialized:
        css_class = "is_online"
    # online + logged in
    if is_online and not in_limbo and is_initialized:
        css_class = "is_online is_initialized"
    # online + logged in + dead
    if is_online and in_limbo and is_initialized:
        css_class = "is_online in_limbo is_initialized"

    return css_class


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
        "current_view", "frontend"
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid)
    elif current_view == "info":
        show_info_view(module, dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid)


def frontend_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('player_table_widget/view_frontend.html')
    template_table_rows = module.templates.get_template('player_table_widget/table_row.html')
    template_table_header = module.templates.get_template('player_table_widget/table_header.html')

    control_info_link = module.templates.get_template('player_table_widget/control_info_link.html')
    control_kick_link = module.templates.get_template('player_table_widget/control_kick_link.html')

    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')

    all_player_dicts = module.dom.data.get(module.get_module_identifier(), {}).get("players", {})
    table_rows = ""
    for steamid, player_dict in all_player_dicts.items():

        if steamid == 'last_updated_servertime':
            continue

        table_rows += template_table_rows.render(
            player=player_dict,
            css_class=get_player_table_row_css_class(player_dict),
            control_info_link=control_info_link.render(
                player=player_dict
            ),
            control_kick_link=control_kick_link.render(
                player=player_dict,
            )
        )

    current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get("current_view", "frontend")

    options_toggle = template_options_toggle.render(
        options_view_toggle=(True if current_view == "frontend" else False),
        steamid=dispatchers_steamid
    )

    data_to_emit = template_frontend.render(
        options_toggle=options_toggle,
        table_rows=table_rows,
        table_header=template_table_header.render()
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "player_table_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('player_table_widget/view_options.html')
    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')

    current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
        "current_view", "frontend"
    )
    options_toggle = template_options_toggle.render(
        options_view_toggle=(True if current_view == "frontend" else False),
        steamid=dispatchers_steamid
    )

    data_to_emit = template_frontend.render(
        options_toggle=options_toggle
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "player_table_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def show_info_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('player_table_widget/view_info.html')
    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')

    current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get("current_view", "frontend")
    current_view_steamid = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get("current_view_steamid", None)
    options_toggle = template_options_toggle.render(
        options_view_toggle=(True if current_view == "frontend" else False),
        steamid=dispatchers_steamid
    )

    data_to_emit = template_frontend.render(
        options_toggle=options_toggle,
        player=module.dom.data.get("module_players", {}).get("players", {}).get(current_view_steamid, None)
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "player_table_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def component_widget(module, event_data, dispatchers_steamid=None):
    current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get("current_view", "frontend")
    if current_view == "frontend":
        template_table_rows = module.templates.get_template('player_table_widget/table_row.html')

        player_dict = module.dom.data.get(module.get_module_identifier(), {}).get("players", {}).get(event_data[1]["row_id"])
        table_row = template_table_rows.render(
            player=player_dict,
            css_class=get_player_table_row_css_class(player_dict)
        )

        module.webserver.send_data_to_client(
            event_data=table_row,
            data_type="table_row",
            clients=[dispatchers_steamid],
            method="append",
            target_element={
                "id": "player_table_widget",
                "type": "tr",
                # "class": get_player_table_row_css_class(player_dict),
                "selector": "body > main > div > div#player_table_widget > table > tbody"
            }
        )


def update_widget(*args, **kwargs):
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    player_entries_to_update = updated_values_dict
    player_clients_to_update = list(module.webserver.connected_clients.keys())

    for clientid in player_clients_to_update:
        try:
            module_players = module.dom.data.get("module_players", {})
            for steamid, player_dict in player_entries_to_update.items():
                current_view = module_players.get("visibility", {}).get(steamid, {}).get("current_view", None)
                if current_view == "frontend":
                    module.webserver.send_data_to_client(
                        event_data=player_dict,
                        data_type="table_row_content",
                        clients=[clientid],
                        method="update",
                        target_element={
                            "id": "player_table_row",
                            "parent_id": "player_table_widget",
                            "module": "players",
                            "type": "tr",
                            "class": get_player_table_row_css_class(player_dict),
                            "selector": "body > main > div > div > table > tbody"
                        }
                    )
                elif current_view == "info":
                    module.webserver.send_data_to_client(
                        event_data=player_dict,
                        data_type="table_row_content",
                        clients=[clientid],
                        method="update",
                        target_element={
                            "id": "player_table_row",
                            "parent_id": "player_table_widget",
                            "module": "players",
                            "type": "tr",
                            "selector": "body > main > div > div > table > tbody"
                        }
                    )
        except AttributeError as error:
            # probably dealing with a player_dict here, not the players dict
            pass
        except KeyError as error:
            pass

    # if len(player_entries_to_update) >= 1:
    #     print("updating player widget for webinterface users {} and players {}".format(
    #         player_clients_to_update,
    #         list(player_entries_to_update.keys())
    #     ))


def update_component(*args, **kwargs):
    module = args[0]
    player_steamid = kwargs.get("updated_values_dict").get("steamid", None)
    player_dict = module.dom.data.get(module.get_module_identifier(), {}).get("players", {}).get(player_steamid, None)

    control_info_link = module.templates.get_template('player_table_widget/control_info_link.html')
    data_to_emit = control_info_link.render(
        player=player_dict
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="element_content",
        clients="all",
        method="update",
        target_element={
            "id": "player_table_row_{}_control_info_link".format(str(player_steamid)),
        }
    )

    control_kick_link = module.templates.get_template('player_table_widget/control_kick_link.html')
    data_to_emit = control_kick_link.render(
        player=player_dict
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="element_content",
        clients="all",
        method="update",
        target_element={
            "id": "player_table_row_{}_control_kick_link".format(str(player_steamid)),
        }
    )

    # print("ONLINE STATUS CHANGED FOR PLAYER {steamid}!!!!!!!".format(steamid=player_steamid))


widget_meta = {
    "description": "sends and updates a table of all currently known players",
    "main_widget": select_view,
    "component_widget": component_widget,
    "handlers": {
        "module_players/visibility/%steamid%/current_view": select_view,
        "module_players/players/%steamid%/is_online": update_component,
        "module_players/players/%steamid%": update_widget,
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
