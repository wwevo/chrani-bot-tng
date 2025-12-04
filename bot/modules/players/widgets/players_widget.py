from pprint import pp

from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]

def select_widget_view(module, callback_meta, dispatchers_id=None):
    dispatchers_id = callback_meta.get("dispatchers_id")
    current_view = module.get_current_view(widget_name, dispatchers_id)
    widget_meta.get("views").get(current_view)(module, callback_meta, dispatchers_id)

def main_view(module, callback_meta, dispatchers_id=None):
    dispatchers_id = callback_meta.get("dispatchers_id")

    widget = module.templates.get_template('players_widget/main/index.html')
    data_to_emit = module.template_render_hook(
        module,
        template=widget,
        title=widget_meta.get("id"),
        navigation=module.webserver.get_navigation_for_widget(module, widget_meta),
        main=widget_meta.get("description")
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_id],
        method="update",
        target_element={
            "id": widget_meta.get("id"),
            "type": "div",
            "selector": "body > main > div"
        }
    )

def options_view(module, callback_meta, dispatchers_id=None):
    dispatchers_id = callback_meta.get("dispatchers_id")

    widget = module.templates.get_template('players_widget/options/index.html')
    data_to_emit = module.template_render_hook(
        module,
        template=widget,
        title="{} - Options".format(widget_meta.get("id")),
        navigation=module.webserver.get_navigation_for_widget(module, widget_meta),
        main="Options",
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_id],
        method="update",
        target_element={
            "id": widget_meta.get("id"),
            "type": "div",
            "selector": "body > main > div"
        }
    )

widget_meta = {
    "id": widget_name,
    "views": {
        "main_view": main_view,
        "options_view": options_view
    },
    "description": "sends and updates a table of all currently known players",
    "main_widget": select_widget_view,
    "handlers": {
        "{}/%dataset%/visibility/%steamid%/{}_view".format("module_" + module_name, widget_name):
            select_widget_view,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
