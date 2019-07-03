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
    elif current_view == "create_new":
        create_new_view(module, dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid)


def frontend_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('locations_widget/view_frontend.html')

    template_options_toggle = module.templates.get_template('locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_create_new_view.html'
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
                options_view_toggle=True
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=True
            )
        )
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('locations_widget/view_options.html')
    template_options_toggle = module.templates.get_template('locations_widget/control_switch_view.html')

    template_options_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_create_new_view.html'
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
                options_view_toggle=False,
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=True,
            )
        ),
        widget_options=module.options,
        available_actions=module.all_available_actions_dict,
        available_widgets=module.all_available_widgets_dict
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def create_new_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('locations_widget/view_create_new.html')

    template_options_toggle = module.templates.get_template('locations_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_options_view.html'
    )

    template_create_new_toggle_view = module.templates.get_template(
        'locations_widget/control_switch_create_new_view.html'
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
                options_view_toggle=True
            ),
            control_switch_create_new_view=module.template_render_hook(
                module,
                template_create_new_toggle_view,
                steamid=dispatchers_steamid,
                create_new_view_toggle=False
            )
        ),
        widget_options=module.options,
        available_actions=module.all_available_actions_dict,
        available_widgets=module.all_available_widgets_dict
    )

    module.webserver.send_data_to_client_hook(
        module,
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "locations_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def update_player_location(*args, **kwargs):
    module = args[0]
    old_values_dict = kwargs.get("old_values_dict", None)
    updated_values_dict = kwargs.get("updated_values_dict", None)


widget_meta = {
    "description": "shows locations and stuff",
    "main_widget": select_view,
    "handlers": {
        "module_locations/visibility/%steamid%/current_view": select_view,
        "module_players/players/%steamid%/pos": update_player_location
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
