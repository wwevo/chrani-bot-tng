from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def main_widget(module, widget, **kwargs):
    if not module.webserver.connected_clients:
        return

    thread_stats = module.dom.data.get("module_game_environment", {}).get("thread_stats")
    if not thread_stats:
        return

    template_frontend = module.templates.get_template('thread_stats_widget.html')
    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        thread_stats=thread_stats
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

    updated_data = widget.get("updated_data")
    thread_stats = updated_data.get("module_game_environment", {}).get("thread_stats")
    if not thread_stats:
        return

    template_frontend = module.templates.get_template('thread_stats_widget.html')
    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        thread_stats=thread_stats
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        target_element=target_element
    )


widget_meta = {
    "id": widget_name,
    "description": "displays thread tracker statistics",
    "main_widget": main_widget,
    "handlers": {
        "module_game_environment/%thread_stats%": update_widget
    },
    "enabled": True
}

target_element = {
    "id": widget_meta.get("id"),
    "type": "div",
    "selector": "body > header > div > div"
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
