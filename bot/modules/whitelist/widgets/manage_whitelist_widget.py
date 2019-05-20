from bot import loaded_modules_dict
from os import path, pardir
from copy import deepcopy

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
    template_frontend = module.templates.get_template('manage_whitelist_widget/view_frontend.html')
    template_table_rows = module.templates.get_template('manage_whitelist_widget/table_row.html')
    template_add_steamid_form = module.templates.get_template('manage_whitelist_widget/add_steamid_form.html')
    template_enable_disable_toggle = module.templates.get_template('manage_whitelist_widget/enable_disable_toggle.html')

    all_player_dicts = deepcopy(module.dom.data.get("module_players", {}).get("players", {}))
    whitelisted_players = module.dom.data.get("module_whitelist", {}).get("players", {})
    for steamid, player_dict in whitelisted_players.items():
        if steamid not in all_player_dicts:
            all_player_dicts[steamid] = player_dict
            all_player_dicts[steamid]["steamid"] = steamid

    table_rows = ""
    for steamid, player_dict in all_player_dicts.items():

        if steamid == 'last_updated_servertime':
            continue

        player_dict_to_add = {}
        player_dict_to_add.update(player_dict)
        player_is_whitelisted = module.dom.data.get("module_whitelist", {}).get("players", {}).get(steamid, None)
        if player_is_whitelisted is not None:
            for key, value in player_is_whitelisted.items():
                player_dict_to_add[key] = value

        table_rows += template_table_rows.render(
            player=player_dict_to_add,
            css_class=get_css_class(player_dict_to_add)
        )

    table_form = template_add_steamid_form.render()
    enable_disable_toggle = template_enable_disable_toggle.render(
        whitelist_status="whitelist is active" if module.dom.data.get("module_whitelist", {}).get("is_active", False) else "whitelist is deactivated",
        enable_disable_toggle=module.dom.data.get("module_whitelist", {}).get("is_active", False)
    )

    data_to_emit = template_frontend.render(
        enable_disable_toggle=enable_disable_toggle,
        table_rows=table_rows,
        table_form=table_form
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


def update_widget(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    """ send updated information to each active client of the webinterface
        widget will update
            whenever the whitelist status of any player changes or
            whenever a new player is added to the player-table
    """
    template_table_rows = module.templates.get_template('manage_whitelist_widget/table_row.html')
    for clientid in module.webserver.connected_clients.keys():
        players_to_update = {}
        for steamid, player_dict_to_update in updated_values_dict.get("players", {}).items():
            player_dict = module.dom.data.get("module_players", {}).get("players", {}).get(steamid, {"steamid": steamid})
            player_dict.update(player_dict_to_update)
            players_to_update[steamid] = player_dict

        for steamid in updated_values_dict.get("online_players", []):
            player_dict = module.dom.data.get("module_players", {}).get("players", {}).get(steamid, {"steamid": steamid})
            player_is_whitelisted = module.dom.data.get("module_whitelist", {}).get("players", {}).get(steamid, None)
            players_to_update[steamid] = player_dict
            if player_is_whitelisted is not None:
                for key, value in player_is_whitelisted.items():
                    players_to_update[steamid][key] = value

        for steamid, player_dict in players_to_update.items():
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
                    "id": "manage_whitelist_table_row_{}".format(player_dict["steamid"]),
                    "parent_id": "manage_whitelist_widget",
                    "module": "whitelist",
                    "type": "tr",
                    "class": get_css_class(player_dict),
                    "selector": "body > main > div > div#manage_whitelist_widget > table > tbody"
                }
            )
            print("updating whitelist widget for webinterface user {} and player {}".format(clientid, player_dict["steamid"]))


def update_widget_status(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    template_enable_disable_toggle = module.templates.get_template('manage_whitelist_widget/enable_disable_toggle.html')
    enable_disable_toggle = template_enable_disable_toggle.render(
        whitelist_status="whitelist is active" if updated_values_dict.get("is_active", False) else "whitelist is deactivated",
        enable_disable_toggle=updated_values_dict.get("is_active", False)
    )
    module.webserver.send_data_to_client(
        event_data=enable_disable_toggle,
        data_type="table_row",
        clients="all",
        method="update",
        target_element={
            "id": "manage_whitelist_widget_status",
            "parent_id": "manage_whitelist_widget",
            "module": "whitelist",
            "type": "tr",
            "selector": "body > main > div > div#manage_whitelist_widget > table > thead"
        }
    )


widget_meta = {
    "description": "manages whitelist entries",
    "main_widget": main_widget,
    "component_widget": update_widget,
    "handlers": {
        "module_whitelist/players": update_widget,
        "module_players/online_players": update_widget,
        "module_whitelist/is_active": update_widget_status
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
