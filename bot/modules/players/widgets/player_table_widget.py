from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def get_css_class(player_dict):
    in_limbo = player_dict["in_limbo"]
    is_online = player_dict["is_online"]

    if in_limbo and is_online:
        css_class = "is_online in_limbo"
    elif not in_limbo and is_online:
        css_class = "is_online"
    elif in_limbo and not is_online:
        css_class = "is_offline in_limbo"
    else:
        css_class = ""

    return css_class


def main_widget(module):
    template_frontend = module.templates.get_template('player_table_widget_frontend.html')
    template_table_rows = module.templates.get_template('player_table_widget_table_row.html')

    all_player_dicts = module.dom.data.get(module.get_module_identifier(), {}).get("players", {})
    table_rows = ""
    for steamid, player_dict in all_player_dicts.items():

        if steamid == 'last_updated':
            continue

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
        clients=module.webserver.connected_clients.keys(),
        method="update",
        target_element={
            "id": "player_table_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def update_widget(module, updated_values_dict, old_values_dict):
    try:
        for steamid, player_dict in updated_values_dict.get("players", {}).items():
            module.webserver.send_data_to_client(
                event_data=player_dict,
                data_type="element_content",
                clients=list(module.webserver.connected_clients.keys()),
                method="update",
                target_element={
                    "id": "player_table_row_{}".format(player_dict["steamid"]),
                    "type": "tr",
                    "dummy_id": "player_table_row_",
                    "class": get_css_class(player_dict),
                    "selector": "body > main > div > div > table > tbody"
                }
            )
    except AttributeError as error:
        pass


widget_meta = {
    "description": "sends and updates a table of all currently known players",
    "main_widget": main_widget,
    "handlers": {
        "players": update_widget
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
