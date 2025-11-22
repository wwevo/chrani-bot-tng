"""
EXAMPLE WIDGET: Checkbox Table

This widget demonstrates the complete pattern for creating tables with selectable checkboxes.

ARCHITECTURE OVERVIEW:
======================

1. DOM STRUCTURE (CRITICAL!):
   module_example_checkboxes/
     elements/                    # Must be called "elements" for dom_management!
       {dataset}/                 # e.g., "example_dataset"
         {item_id}/              # e.g., "item_001"
           id: str
           owner: str             # Usually same as item_id
           identifier: str        # Usually same as item_id
           name: str              # Display name
           description: str       # Any data you want
           dataset: str           # Dataset name
           selected_by: []        # List of steamids who selected this

2. HANDLERS:
   - main_widget: Called on connect and view changes
   - elements/{dataset}/{id}: Called when new items added or updated
   - elements/{dataset}/{id}/selected_by: Called when checkbox clicked

3. FLOW:
   User clicks checkbox
     → Browser sends socket.emit('widget_event', ['dom_management', ['select', {...}]])
     → dom_management/select action updates selected_by in DOM
     → DOM fires callback to: module_example_checkboxes/elements/{dataset}/{id}/selected_by
     → update_selection_status() handler re-renders checkbox
     → Browser updates ONLY the checkbox span (granular update)
"""

from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]

VIEW_REGISTRY = {
    'frontend': {
        'label_active': 'back',
        'label_inactive': 'main',
        'action': 'show_frontend',
        'include_in_menu': False
    },
    'options': {
        'label_active': 'back',
        'label_inactive': 'options',
        'action': 'show_options',
        'include_in_menu': True
    }
}


def select_view(*args, **kwargs):
    """Main entry point - router for different views"""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)
    
    current_view = module.get_current_view(dispatchers_steamid)
    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


def frontend_view(*args, **kwargs):
    """Shows the checkbox table"""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    # Load all templates
    template_main = module.templates.get_template('checkbox_widget/view_main.html')
    template_table_header = module.templates.get_template('checkbox_widget/table_header.html')
    template_table_row = module.templates.get_template('checkbox_widget/table_row.html')
    template_table_footer = module.templates.get_template('checkbox_widget/table_footer.html')
    template_view_menu = module.templates.get_template('checkbox_widget/control_view_menu.html')

    # Get all elements from DOM
    all_elements = module.dom.data.get("module_example_checkboxes", {}).get("elements", {})
    
    # Get current view for view menu
    current_view = module.get_current_view(dispatchers_steamid)

    # Build table rows
    table_rows_list = []
    for dataset, items in all_elements.items():
        for item_id, item_data in items.items():
            # Check if this item is selected by current user
            item_is_selected_by = item_data.get("selected_by", [])
            item_entry_selected = dispatchers_steamid in item_is_selected_by

            # CRITICAL: Generate control_select_link with original item_data
            # This MUST be done BEFORE sanitizing the dataset for HTML IDs
            control_select_link = module.dom_management.get_selection_dom_element(
                module,
                target_module="module_example_checkboxes",
                dom_element_select_root=["selected_by"],  # Just ["selected_by"], not full path!
                dom_element=item_data,
                dom_element_entry_selected=item_entry_selected,
                dom_action_inactive="select_dom_element",
                dom_action_active="deselect_dom_element"
            )

            # Now prepare sanitized data for template
            item_dict_for_template = item_data.copy()
            item_dict_for_template["dataset"] = module.dom_management.sanitize_for_html_id(dataset)
            item_dict_for_template["dataset_original"] = dataset

            # Render row with control
            rendered_row = module.template_render_hook(
                module,
                template=template_table_row,
                item=item_dict_for_template,
                control_select_link=control_select_link
            )
            table_rows_list.append(rendered_row)

    table_rows = ''.join(table_rows_list) if table_rows_list else '<tr><td colspan="3">No items yet</td></tr>'

    # Render view menu
    options_toggle = module.template_render_hook(
        module,
        template=template_view_menu,
        views=VIEW_REGISTRY,
        current_view=current_view,
        steamid=dispatchers_steamid
    )

    # Render complete view
    data_to_emit = module.template_render_hook(
        module,
        template=template_main,
        options_toggle=options_toggle,
        table_header=module.template_render_hook(module, template=template_table_header),
        table_rows=table_rows,
        table_footer=module.template_render_hook(module, template=template_table_footer)
    )

    # Send to client
    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "checkbox_widget",
            "type": "div",
            "selector": "body > main > div"
        }
    )


def options_view(*args, **kwargs):
    """Shows the options view"""
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)
    
    # Load templates
    template_options = module.templates.get_template('checkbox_widget/view_options.html')
    template_view_menu = module.templates.get_template('checkbox_widget/control_view_menu.html')
    
    # Get current view for view menu
    current_view = module.get_current_view(dispatchers_steamid)
    
    # Render view menu
    options_toggle = module.template_render_hook(
        module,
        template=template_view_menu,
        views=VIEW_REGISTRY,
        current_view=current_view,
        steamid=dispatchers_steamid
    )
    
    # Render options view
    data_to_emit = module.template_render_hook(
        module,
        template=template_options,
        options_toggle=options_toggle
    )
    
    # Send to client
    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="widget_content",
        clients=[dispatchers_steamid],
        method="update",
        target_element={
            "id": "checkbox_widget",
            "type": "div",
            "selector": "body > main > div"
        }
    )


def table_rows(*args, **kwargs):
    """
    Handler for new/updated items.
    Called when DOM path: module_example_checkboxes/elements/{dataset}/{id} changes
    """
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)
    method = kwargs.get("method", None)

    if method in ["upsert", "edit", "insert", "update"]:
        template_table_row = module.templates.get_template('checkbox_widget/table_row.html')

        for clientid in module.webserver.connected_clients.keys():
            for item_id, item_data in updated_values_dict.items():
                # Get selected_by from full DOM data
                dataset = item_data.get("dataset", "unknown")
                item_is_selected_by = (
                    module.dom.data
                    .get("module_example_checkboxes", {})
                    .get("elements", {})
                    .get(dataset, {})
                    .get(item_id, {})
                    .get("selected_by", [])
                )

                item_entry_selected = clientid in item_is_selected_by

                # Generate control_select_link
                control_select_link = module.dom_management.get_selection_dom_element(
                    module,
                    target_module="module_example_checkboxes",
                    dom_element_select_root=["selected_by"],
                    dom_element=item_data,
                    dom_element_entry_selected=item_entry_selected,
                    dom_action_inactive="select_dom_element",
                    dom_action_active="deselect_dom_element"
                )

                # Prepare template data
                item_dict_for_template = item_data.copy()
                item_dict_for_template["dataset"] = module.dom_management.sanitize_for_html_id(dataset)
                item_dict_for_template["dataset_original"] = dataset

                # Render row
                table_row = module.template_render_hook(
                    module,
                    template=template_table_row,
                    item=item_dict_for_template,
                    control_select_link=control_select_link
                )

                # Send to client (will upsert/insert row in table)
                sanitized_dataset = item_dict_for_template["dataset"]
                table_row_id = "checkbox_table_row_{}_{}".format(sanitized_dataset, item_id)

                module.webserver.send_data_to_client_hook(
                    module,
                    payload=table_row,
                    data_type="table_row",
                    clients=[clientid],
                    target_element={
                        "id": table_row_id,
                        "type": "tr",
                        "selector": "body > main > div > div#checkbox_widget > main > table > tbody#checkbox_table"
                    }
                )


def update_selection_status(*args, **kwargs):
    """
    Handler for checkbox selection changes.
    Called when DOM path: module_example_checkboxes/elements/{dataset}/{id}/selected_by changes

    This handler ONLY updates the checkbox control span - ultra-granular update!
    """
    module = args[0]
    updated_values_dict = kwargs.get("updated_values_dict", None)

    # Sanitize dataset for HTML ID
    sanitized_dataset = module.dom_management.sanitize_for_html_id(updated_values_dict["dataset"])

    # Call dom_management helper to update the checkbox
    module.dom_management.update_selection_status(
        *args, **kwargs,
        target_module=module,
        dom_action_active="deselect_dom_element",
        dom_action_inactive="select_dom_element",
        dom_element_id={
            "id": "checkbox_table_row_{}_{}_control_select_link".format(
                sanitized_dataset,
                updated_values_dict["identifier"]
            )
        }
    )


# Widget registration
widget_meta = {
    "description": "Example widget demonstrating checkbox table pattern",
    "main_widget": select_view,
    "handlers": {
        # Called when new items are added or updated
        "module_example_checkboxes/elements/%dataset%/%element_identifier%":
            table_rows,
        # Called when checkbox is clicked (selected_by changes)
        "module_example_checkboxes/elements/%dataset%/%element_identifier%/selected_by":
            update_selection_status,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
