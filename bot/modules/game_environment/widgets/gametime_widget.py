from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]

def main_widget(module, widget, **kwargs):
    if not module.webserver.connected_clients:
        return

    active_dataset = module.dom.data.get("module_game_environment", {}).get("active_dataset")
    if not active_dataset:
        return

    last_recorded_gametime = module.dom.data.get("module_game_environment").get(active_dataset).get("last_recorded_gametime")
    if not last_recorded_gametime:
        return

    template_frontend = module.templates.get_template('gametime_widget.html')
    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        last_recorded_gametime=last_recorded_gametime
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        target_element=target_element
    )


def update_widget(module, widget, dispatchers_id=None):
    if not module.webserver.connected_clients:
        return

    active_dataset = module.dom.data.get("module_game_environment").get("active_dataset")
    if not active_dataset:
        return

    updated_data = widget.get("updated_data")
    last_recorded_gametime = updated_data.get("module_game_environment").get(active_dataset).get("last_recorded_gametime")
    if not last_recorded_gametime:
        return

    template_frontend = module.templates.get_template('gametime_widget.html')
    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        last_recorded_gametime=last_recorded_gametime
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        target_element=target_element
    )


widget_meta = {
    "id": widget_name,
    "description": "displays the in-game time and day",
    "main_widget": main_widget,
    "handlers": {
        "module_game_environment/%dataset%/%last_recorded_gametime%": update_widget
    },
    "enabled": True
}

target_element = {
    "id": widget_meta.get("id"),
    "type": "div",
    "selector": "body > header > div > div"
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
