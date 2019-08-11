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
        "widget_handling", {}
    ).get(
        "current_view", "frontend"
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    template_frontend = module.templates.get_template('widget_handling/view_frontend.html')
    template_options_toggle = module.templates.get_template('widget_handling/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'widget_handling/control_switch_options_view.html'
    )

    current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(
        dispatchers_steamid, {}
    ).get(
        "widget_handling", {}
    ).get(
        "current_view", "frontend"
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
                options_view_toggle=(True if current_view == "frontend" else False)
            ),
        )
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "widget_handling",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get("dispatchers_steamid", None)

    template_frontend = module.templates.get_template('widget_handling/view_options.html')

    template_options_toggle = module.templates.get_template('widget_handling/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'widget_handling/control_switch_options_view.html'
    )

    current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(
        dispatchers_steamid, {}
    ).get(
        "widget_handling", {}
    ).get(
        "current_view", "frontend"
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
                options_view_toggle=(True if current_view == "frontend" else False)
            ),
        )
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "widget_handling",
            "type": "table",
            "selector": "body > main > div"
        }
    )


widget_meta = {
    "description": "controls widget handling. enabling, change their appearance.",
    "main_widget": select_view,
    "handlers": {
        "module_webserver/visibility/%steamid%/widget_handling/current_view": select_view,
    },
    "enabled": False
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
