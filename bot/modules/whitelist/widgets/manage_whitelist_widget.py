from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_css_class(player_dict):
    on_whitelist = player_dict.get("on_whitelist", False)
    is_banned = player_dict.get("is_banned", False)

    if on_whitelist and is_banned:
        css_class = "on_whitelist is_banned"
    elif is_banned:
        css_class = "is_banned"
    elif on_whitelist:
        css_class = "on_whitelist"
    else:
        css_class = ""

    return css_class


def main_widget(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('manage_whitelist_widget_frontend.html')
    template_table_rows = module.templates.get_template('manage_whitelist_widget_table_row.html')

    all_player_dicts = module.dom.data.get("module_players", {}).get("players", {})

    table_rows = ""
    for steamid, player_dict in all_player_dicts.items():

        if steamid == 'last_updated':
            continue

        player_is_whitelisted = module.dom.data.get("module_whitelist", {}).get("players", {}).get(steamid, None)
        if player_is_whitelisted is not None:
            for key, value in player_is_whitelisted.items():
                player_dict[key] = value

        table_rows += template_table_rows.render(
            player=player_dict,
            css_class=get_css_class(player_dict)
        )

    data_to_emit = template_frontend.render(
        table_rows=table_rows
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "manage_whitelist_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def update_widget(module, updated_values_dict=None, old_values_dict=None):
    template_table_rows = module.templates.get_template('manage_whitelist_widget_table_row.html')

    for clientid in module.webserver.connected_clients.keys():
        try:
            for steamid, player_dict_to_update in updated_values_dict.get("players", {}).items():
                player_dict = module.dom.data.get("module_players", {}).get("players", {}).get(steamid)
                player_dict.update(player_dict_to_update)
                table_row = template_table_rows.render(
                    player=player_dict,
                    css_class=get_css_class(player_dict)
                )
                module.webserver.send_data_to_client(
                    event_data=table_row,
                    data_type="table_row",
                    clients=[clientid],
                    method="update",
                    target_element={
                        "id": "manage_whitelist_table_row_{}".format(steamid),
                        "parent_id": "manage_whitelist_widget",
                        "module": "whitelist",
                        "type": "tr",
                        "class": get_css_class(player_dict_to_update),
                        "selector": "body > main > div > div > table > tbody"
                    }
                )
                print("updating whitelist widget for webinterface user {} and player {}".format(clientid, steamid))
        except KeyError as error:
            pass


widget_meta = {
    "description": "manages whitelist entries",
    "main_widget": main_widget,
    "handlers": {
        "module_whitelist/players": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
