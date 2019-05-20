from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_player_table_row_css_class(player_dict):
    in_limbo = player_dict.get("in_limbo", False)
    is_online = player_dict.get("is_online", False)

    if in_limbo and is_online:
        css_class = "is_online in_limbo"
    elif not in_limbo and is_online:
        css_class = "is_online"
    elif in_limbo and not is_online:
        css_class = "is_offline in_limbo"
    else:
        css_class = ""

    return css_class


def select_view(module, *args, **kwargs):
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


def options_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('player_table_widget/view_options.html')
    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')
    current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
        "current_view", "frontend"
    )
    if current_view == "frontend":
        options_view_toggle = True
    else:
        options_view_toggle = False

    options_toggle = template_options_toggle.render(
        options_view_toggle=options_view_toggle,
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
    pass


def show_info_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('player_table_widget/view_info.html')
    template_options_toggle = module.templates.get_template('player_table_widget/control_switch_view.html')
    current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get("current_view", "frontend")
    current_view_steamid = module.dom.data.get("module_players", {}).get("visibility", {}).get(dispatchers_steamid, {}).get("current_view_steamid", None)

    if current_view == "frontend":
        options_view_toggle = True
    else:
        options_view_toggle = False

    options_toggle = template_options_toggle.render(
        options_view_toggle=options_view_toggle,
        steamid=dispatchers_steamid
    )

    data_to_emit = template_frontend.render(
        options_toggle=options_toggle,
        current_view_steamid=current_view_steamid,
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
    pass


def frontend_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('player_table_widget/view_frontend.html')
    template_table_rows = module.templates.get_template('player_table_widget/table_row.html')
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
    if current_view == "frontend":
        options_view_toggle = True
    else:
        options_view_toggle = False

    options_toggle = template_options_toggle.render(
        options_view_toggle=options_view_toggle,
        steamid=dispatchers_steamid
    )

    data_to_emit = template_frontend.render(
        options_toggle=options_toggle,
        table_rows=table_rows
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


def update_widget(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    for clientid in module.webserver.connected_clients.keys():
        try:
            for steamid, player_dict in updated_values_dict.get("players", {}).items():
                current_view = module.dom.data.get("module_players", {}).get("visibility", {}).get(steamid,{}).get("current_view", None)
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
                    print("updating player widget for webinterface user {} and player {}".format(clientid, steamid))
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
                    print("updating player widget for webinterface user {} and player {}".format(clientid, steamid))
        except KeyError as error:
            pass


def test(*args, **kwargs):
    print("ONLINE STATUS CHANGED FOR PLAYER {steamid}!!!!!!!".format(steamid=kwargs.get("updated_values_dict").get("steamid")))


widget_meta = {
    "description": "sends and updates a table of all currently known players",
    "main_widget": select_view,
    "component_widget": component_widget,
    "handlers": {
        "module_players/visibility/%steamid%/current_view": select_view,
        "module_players/players/%steamid%/is_online": test,
        "module_players/players/%steamid%/in_limbo": test,
        "module_players/players": update_widget,
        "module_players/players//%steamid%/last_seen_gametime": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
