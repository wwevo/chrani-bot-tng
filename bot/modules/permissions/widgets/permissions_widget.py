from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
        "current_view", "frontend"
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid)


def frontend_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('permissions_widget/view_frontend.html')

    template_options_toggle = module.templates.get_template('permissions_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'permissions_widget/control_switch_options_view.html'
    )

    current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
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
            )
        )
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "permissions_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('permissions_widget/view_options.html')

    template_options_toggle = module.templates.get_template('permissions_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'permissions_widget/control_switch_options_view.html'
    )

    current_view = module.dom.data.get(module.get_module_identifier(), {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
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
            )
        ),
        widget_options=module.options,
        available_actions=module.all_available_actions_dict,
        available_widgets=module.all_available_widgets_dict
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "permissions_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


widget_meta = {
    "description": "shows permissions and stuff",
    "main_widget": select_view,
    "handlers": {
        "module_permissions/visibility/%steamid%/current_view": select_view
    },
    "enabled": False
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
