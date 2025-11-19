from bot import loaded_modules_dict
from os import path, pardir, listdir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


def select_view(*args, **kwargs):
    """Selects which view to display based on current_view setting."""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    current_view = module.get_current_view(dispatchers_steamid)

    if current_view == "scenarios":
        scenarios_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    """Main testing control panel view."""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_frontend = module.templates.get_template('testing_control_widget/view_frontend.html')
    template_options_toggle = module.templates.get_template('testing_control_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('testing_control_widget/control_switch_options_view.html')

    # Get available scenarios
    module_dir = path.dirname(path.abspath(path.join(__file__, pardir, pardir)))
    scenarios_dir = path.join(module_dir, "scenarios")
    available_scenarios = get_available_scenarios(scenarios_dir)

    # Get testing module stats
    testing_data = module.dom.data.get(module.get_module_identifier(), {})
    injection_count = testing_data.get("injection_count", 0)
    last_injected = testing_data.get("last_injected_line", "None")
    scenarios_loaded = testing_data.get("scenarios_loaded", [])

    current_view = module.get_current_view(dispatchers_steamid)

    options_toggle = module.template_render_hook(
        module,
        template=template_options_toggle,
        control_switch_options_view=module.template_render_hook(
            module,
            template=template_options_toggle_view,
            options_view_toggle=(current_view in ["frontend"]),
            steamid=dispatchers_steamid
        )
    )

    data_to_emit = module.template_render_hook(
        module,
        template=template_frontend,
        options_toggle=options_toggle,
        available_scenarios=available_scenarios,
        injection_count=injection_count,
        last_injected_line=last_injected,
        scenarios_loaded=scenarios_loaded,
        steamid=dispatchers_steamid
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "testing_control_widget",
            "type": "div",
            "selector": "body > main > div"
        }
    )


def scenarios_view(*args, **kwargs):
    """Scenarios library view."""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    template_scenarios = module.templates.get_template('testing_control_widget/view_scenarios.html')
    template_options_toggle = module.templates.get_template('testing_control_widget/control_switch_view.html')
    template_options_toggle_view = module.templates.get_template('testing_control_widget/control_switch_options_view.html')

    # Get available scenarios with their details
    module_dir = path.dirname(path.abspath(path.join(__file__, pardir, pardir)))
    scenarios_dir = path.join(module_dir, "scenarios")
    available_scenarios = get_scenario_details(scenarios_dir)

    current_view = module.get_current_view(dispatchers_steamid)

    options_toggle = module.template_render_hook(
        module,
        template=template_options_toggle,
        control_switch_options_view=module.template_render_hook(
            module,
            template=template_options_toggle_view,
            options_view_toggle=(current_view in ["scenarios"]),
            steamid=dispatchers_steamid
        )
    )

    data_to_emit = module.template_render_hook(
        module,
        template=template_scenarios,
        options_toggle=options_toggle,
        scenarios=available_scenarios,
        steamid=dispatchers_steamid
    )

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "testing_control_widget",
            "type": "div",
            "selector": "body > main > div"
        }
    )


def update_widget(*args, **kwargs):
    """Updates the widget when testing data changes."""
    module = args[0]

    # Refresh widget for all connected clients
    for clientid in module.webserver.connected_clients.keys():
        current_view = module.get_current_view(clientid)
        if current_view == "frontend":
            frontend_view(module, dispatchers_steamid=clientid)
        elif current_view == "scenarios":
            scenarios_view(module, dispatchers_steamid=clientid)


def get_available_scenarios(scenarios_dir):
    """Returns list of available scenario names."""
    if not path.exists(scenarios_dir):
        return []

    scenarios = []
    for filename in listdir(scenarios_dir):
        if filename.endswith('.json'):
            scenarios.append(filename[:-5])  # Remove .json extension
    return scenarios


def get_scenario_details(scenarios_dir):
    """Returns list of scenarios with their metadata."""
    import json

    if not path.exists(scenarios_dir):
        return []

    scenarios = []
    for filename in listdir(scenarios_dir):
        if filename.endswith('.json'):
            scenario_file = path.join(scenarios_dir, filename)
            try:
                with open(scenario_file, 'r') as f:
                    scenario_data = json.load(f)
                    scenarios.append({
                        "id": filename[:-5],
                        "name": scenario_data.get("name", filename[:-5]),
                        "description": scenario_data.get("description", ""),
                        "action_count": len(scenario_data.get("actions", []))
                    })
            except (json.JSONDecodeError, IOError):
                pass
    return scenarios


widget_meta = {
    "description": "Testing control panel for injecting test data",
    "main_widget": select_view,
    "handlers": {
        "module_testing/last_injected_line": update_widget,
        "module_testing/injection_count": update_widget,
        "module_testing/scenarios_loaded": update_widget,
        "module_testing/visibility/%steamid%/current_view": select_view,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
