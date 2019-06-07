from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = module.dom.data.get("module_webserver", {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
        "current_view", "frontend"
    )

    if current_view == "options":
        options_view(module, dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid)


def frontend_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('webserver_status_widget/view_frontend.html')
    template_servertime = module.templates.get_template('webserver_status_widget/control_servertime.html')

    template_options_toggle = module.templates.get_template('webserver_status_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'webserver_status_widget/control_switch_options_view.html'
    )

    component_logged_in_users = module.templates.get_template('webserver_status_widget/component_logged_in_users.html')

    try:
        server_is_online = module.dom.data.get("module_telnet").get("server_is_online", True)
    except AttributeError as error:
        server_is_online = True

    current_view = module.dom.data.get("module_webserver", {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
        "current_view", "frontend"
    )

    webserver_logged_in_users = module.dom.data.get(module.get_module_identifier(), {}).get(
        "webserver_logged_in_users", {}
    )
    data_to_emit = template_frontend.render(
        component_logged_in_users=component_logged_in_users.render(
            webserver_logged_in_users=webserver_logged_in_users
        ),
        options_toggle=template_options_toggle.render(
            control_switch_options_view=template_options_toggle_view.render(
                steamid=dispatchers_steamid,
                options_view_toggle=(True if current_view == "frontend" else False)
            ),
            control_servertime=template_servertime.render(
                time=module.dom.data.get("module_telnet").get("last_recorded_servertime", None),
            )
        ),
        server_is_online=server_is_online
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "webserver_status_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def options_view(module, dispatchers_steamid=None):
    template_frontend = module.templates.get_template('webserver_status_widget/view_options.html')
    template_servertime = module.templates.get_template('webserver_status_widget/control_servertime.html')

    template_options_toggle = module.templates.get_template('webserver_status_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template(
        'webserver_status_widget/control_switch_options_view.html'
    )

    current_view = module.dom.data.get("module_webserver", {}).get("visibility", {}).get(dispatchers_steamid, {}).get(
        "current_view", "frontend"
    )

    data_to_emit = template_frontend.render(
        options_toggle=template_options_toggle.render(
            control_switch_options_view=template_options_toggle_view.render(
                steamid=dispatchers_steamid,
                options_view_toggle=(True if current_view == "frontend" else False)
            ),
            control_servertime=template_servertime.render(
                time=module.dom.data.get("module_telnet").get("last_recorded_servertime", None),
            )
        )
    )

    module.webserver.send_data_to_client(
        event_data=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "webserver_status_widget",
            "type": "table",
            "selector": "body > main > div"
        }
    )


def update_servertime(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    template_servertime = module.templates.get_template('webserver_status_widget/control_servertime.html')
    servertime_view=template_servertime.render(
        time=module.dom.data.get("module_telnet").get("last_recorded_servertime", None)
    )

    module.webserver.send_data_to_client(
        event_data=servertime_view,
        data_type="element_content",
        method="replace",
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "server_status_widget_servertime"
        }
    )


def update_logged_in_users(module, updated_values_dict=None, old_values_dict=None, dispatchers_steamid=None):
    webserver_logged_in_users = updated_values_dict.get("webserver_logged_in_users", {})
    old_webserver_logged_in_users = old_values_dict.get("webserver_logged_in_users", {})

    component_logged_in_users = module.templates.get_template('webserver_status_widget/component_logged_in_users.html')
    component_logged_in_users_view = component_logged_in_users.render(
        webserver_logged_in_users=webserver_logged_in_users
    )

    module.webserver.send_data_to_client(
        event_data=component_logged_in_users_view,
        data_type="element_content",
        method="replace",
        clients=module.webserver.connected_clients.keys(),
        target_element={
            "id": "server_status_widget_logged_in_users"
        }
    )


widget_meta = {
    "description": "shows all users with an active session for the webinterface",
    "main_widget": select_view,
    "handlers": {
        "module_webserver/visibility/%steamid%/current_view": select_view,
        "module_environment/webserver_logged_in_users": update_logged_in_users,
        "module_telnet/last_recorded_servertime": update_servertime
    }
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
