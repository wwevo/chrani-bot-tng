"""
═══════════════════════════════════════════════════════════════════════════════
TUTORIAL MODULE: Checkbox Table Widget with View Toggle
═══════════════════════════════════════════════════════════════════════════════

This is a COMPLETE REFERENCE IMPLEMENTATION demonstrating:
1. ✓ Checkbox tables with selectable rows
2. ✓ Reactive view toggles (Options ↔ Frontend)
3. ✓ Granular DOM updates (only changed elements)
4. ✓ Proper handler registration

Use this module as a template for new widgets!


═══ 1. DOM STRUCTURE (CRITICAL!) ═══════════════════════════════════════════

All selectable elements MUST be stored under: {module}/elements/{dataset}/{id}

module_example_checkboxes/
  elements/                    # ← MUST be called "elements" (dom_management hardcodes this)
    {dataset}/                 # e.g., "example_dataset" (map/server name)
      {item_id}/              # e.g., "item_001"
        id: str               # Unique identifier
        owner: str            # Usually same as item_id
        identifier: str       # Usually same as item_id
        name: str             # Display data
        description: str      # Any additional data
        dataset: str          # Dataset name (for multi-dataset support)
        selected_by: []       # List of steamids who selected this item


═══ 2. HANDLERS (3 types) ═════════════════════════════════════════════════

A. visibility/%steamid%/current_view
   → Called when user toggles view (Options ↔ Frontend)
   → Triggers: select_view() to re-render entire widget
   → FIX #3: This handler was missing initially!

B. elements/%dataset%/%element_identifier%
   → Called when new items added or existing items updated
   → Triggers: table_rows() to render/update rows

C. elements/%dataset%/%element_identifier%/selected_by
   → Called when checkbox clicked (selected_by list changes)
   → Triggers: update_selection_status() to update ONLY the checkbox


═══ 3. DATA FLOW (Checkbox Click) ═════════════════════════════════════════

User clicks checkbox
  ↓
Browser: socket.emit('widget_event', ['dom_management', ['select', {
  'action': 'select_dom_element',
  'target_module': 'module_example_checkboxes',
  'dom_element_select_root': ['selected_by'],
  'dom_element_origin': 'example_dataset',
  'dom_element_owner': 'item_001',
  'dom_element_identifier': 'item_001'
}]])
  ↓
dom_management/select action updates DOM:
  module_example_checkboxes/elements/example_dataset/item_001/selected_by
  (adds/removes steamid from list)
  ↓
DOM fires callback → update_selection_status()
  ↓
Browser receives granular update (ONLY checkbox span, not entire row!)


═══ 4. VIEW TOGGLE FLOW (Options ↔ Frontend) ═════════════════════════════

User clicks "options" link
  ↓
Browser: socket.emit('widget_event', ['example_checkboxes', ['toggle_example_checkboxes_widget_view', {
  'steamid': '76561198012345678',
  'action': 'show_options'
}]])
  ↓
Action: toggle_example_checkboxes_widget_view.py
  → Calls: module.set_current_view(steamid, {'current_view': 'options'})
  ↓
set_current_view() updates DOM:
  module_example_checkboxes/visibility/{steamid}/current_view = 'options'
  ↓
DOM fires callback → visibility handler → select_view()
  ↓
select_view() routes to options_view()
  ↓
Browser receives full widget update (entire options view)


═══ 5. COMMON BUGS (Fixed in this module) ════════════════════════════════

BUG #1: Wrong module name in template
  File: control_view_menu.html line 7-8
  Error: Copy-paste 'game_environment' instead of 'example_checkboxes'
  Fix: Use correct module name in socket.emit events

BUG #2: Missing widget_options variable
  File: checkbox_widget.py options_view() line 184
  Error: Template expects widget_options, not passed to template_render_hook
  Fix: Pass widget_options=module.options

BUG #3: Missing visibility handler
  File: checkbox_widget.py widget_meta line 304-305
  Error: No handler registered for visibility/%steamid%/current_view
  Fix: Add handler that calls select_view()

BUG #4: Missing options_view_toggle variable
  File: checkbox_widget.py line 131 + 178
  Error: Template expects options_view_toggle to compute toggle state
  Fix: Pass options_view_toggle=(current_view == "frontend") or False

"""

from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
widget_name = path.basename(path.abspath(__file__))[:-3]


# ═══════════════════════════════════════════════════════════════════════════
# VIEW REGISTRY - Defines all available views for this widget
# ═══════════════════════════════════════════════════════════════════════════
# This dict configures which views exist and how they're labeled.
# Used by construct_toggle_link macro in templates to generate toggle links.
#
# Fields:
#   label_active:   Text shown when THIS view is active (usually "back")
#   label_inactive: Text shown when OTHER view is active (e.g., "options")
#   action:         Action name to trigger (maps to toggle_*_widget_view.py)
#   include_in_menu: Whether to show in view menu (False for default view)
VIEW_REGISTRY = {
    'frontend': {
        'label_active': 'back',
        'label_inactive': 'main',
        'action': 'show_frontend',
        'include_in_menu': False  # Default view, no explicit menu entry
    },
    'options': {
        'label_active': 'back',
        'label_inactive': 'options',
        'action': 'show_options',
        'include_in_menu': True   # Show "options" link in menu
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# DELETE MODAL VIEW - Confirmation dialog for deleting selected items
# ═══════════════════════════════════════════════════════════════════════════
def delete_modal_view(*args, **kwargs):
    """
    Renders the delete confirmation modal.
    
    This view is triggered when user clicks the delete button.
    It counts selected items and displays a confirmation dialog.
    """
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    all_available_elements = module.dom.data.get("module_example_checkboxes", {}).get("elements", {})
    all_selected_elements_count = 0
    
    for dataset, items in all_available_elements.items():
        for item_id, item_data in items.items():
            item_is_selected_by = item_data.get("selected_by", [])
            if dispatchers_steamid in item_is_selected_by:
                all_selected_elements_count += 1

    modal_confirm_delete = module.dom_management.get_delete_confirm_modal(
        module,
        count=all_selected_elements_count,
        target_module="module_example_checkboxes",
        dom_element_id="checkbox_table_modal_action_delete_button",
        dom_action="delete_selected_dom_elements",
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        confirmed="True"
    )

    data_to_emit = modal_confirm_delete

    module.webserver.send_data_to_client_hook(
        module,
        payload=data_to_emit,
        data_type="modal_content",
        clients=[dispatchers_steamid],
        target_element={
            "id": "checkbox_widget_modal",
            "type": "div",
            "selector": "body > main > div"
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# VIEW ROUTER - Entry point for all widget rendering
# ═══════════════════════════════════════════════════════════════════════════
def select_view(*args, **kwargs):
    """
    Main entry point - routes to correct view based on current_view state.
    
    This function is called:
    - On socket connect (user opens page)
    - When visibility/%steamid%/current_view changes (view toggle)
    
    It reads the current view from DOM and routes to the appropriate view function.
    """
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)
    
    # Get current view from DOM (default: "frontend")
    current_view = module.get_current_view(dispatchers_steamid)
    
    # Route to appropriate view function
    if current_view == "options":
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    elif current_view == "delete-modal":
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)
        delete_modal_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)


# ═══════════════════════════════════════════════════════════════════════════
# FRONTEND VIEW - Main checkbox table view
# ═══════════════════════════════════════════════════════════════════════════
def frontend_view(*args, **kwargs):
    """
    Renders the main checkbox table with all items.
    
    This view shows:
    - View toggle menu (options link)
    - Table header
    - Table rows with checkboxes
    - Table footer
    
    Each row includes a checkbox control that:
    - Shows checked/unchecked state based on selected_by list
    - Sends select/deselect events to dom_management on click
    """
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)

    # Load all templates (micro-template pattern for granular updates)
    template_main = module.templates.get_template('checkbox_widget/view_main.html')
    template_table_header = module.templates.get_template('checkbox_widget/table_header.html')
    template_table_row = module.templates.get_template('checkbox_widget/table_row.html')
    template_table_footer = module.templates.get_template('checkbox_widget/table_footer.html')
    template_view_menu = module.templates.get_template('checkbox_widget/control_view_menu.html')

    # Get all elements from DOM
    all_elements = module.dom.data.get("module_example_checkboxes", {}).get("elements", {})
    
    # Get current view for view menu
    current_view = module.get_current_view(dispatchers_steamid)

    # Build table rows and count selected items
    table_rows_list = []
    all_selected_elements_count = 0
    for dataset, items in all_elements.items():
        for item_id, item_data in items.items():
            # Check if this item is selected by current user
            item_is_selected_by = item_data.get("selected_by", [])
            item_entry_selected = dispatchers_steamid in item_is_selected_by
            
            if item_entry_selected:
                all_selected_elements_count += 1

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

    # ─────────────────────────────────────────────────────────────────────────
    # Render view toggle menu
    # ─────────────────────────────────────────────────────────────────────────
    # CRITICAL: Must pass options_view_toggle variable!
    # This tells construct_toggle_link macro whether to show "options" or "back" link.
    # 
    # BUG #4 Fix: This variable was missing initially, causing toggle to not work.
    # Value: True when in frontend (show "options" link), False when in options (show "back")
    options_toggle = module.template_render_hook(
        module,
        template=template_view_menu,
        views=VIEW_REGISTRY,
        current_view=current_view,
        steamid=dispatchers_steamid,
        options_view_toggle=(current_view == "frontend")  # True = show "options" link
    )

    # Generate delete button
    dom_element_delete_button = module.dom_management.get_delete_button_dom_element(
        module,
        count=all_selected_elements_count,
        target_module="module_example_checkboxes",
        dom_element_id="checkbox_table_widget_action_delete_button",
        dom_action="delete_selected_dom_elements",
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root
    )

    # Render complete view
    data_to_emit = module.template_render_hook(
        module,
        template=template_main,
        options_toggle=options_toggle,
        table_header=module.template_render_hook(module, template=template_table_header),
        table_rows=table_rows,
        table_footer=module.template_render_hook(
            module,
            template=template_table_footer,
            action_delete_button=dom_element_delete_button
        )
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


# ═══════════════════════════════════════════════════════════════════════════
# OPTIONS VIEW - Widget configuration/settings view
# ═══════════════════════════════════════════════════════════════════════════
def options_view(*args, **kwargs):
    """
    Renders the widget options/settings view.
    
    This view shows:
    - View toggle menu (back link)
    - Widget options table
    
    Displays all module.options as key-value pairs in a table.
    """
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)
    
    # Load templates
    template_options = module.templates.get_template('checkbox_widget/view_options.html')
    template_view_menu = module.templates.get_template('checkbox_widget/control_view_menu.html')
    
    # Get current view for view menu
    current_view = module.get_current_view(dispatchers_steamid)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Render view toggle menu
    # ─────────────────────────────────────────────────────────────────────────
    # BUG #4 Fix: options_view_toggle must be False here (we're IN options, show "back")
    options_toggle = module.template_render_hook(
        module,
        template=template_view_menu,
        views=VIEW_REGISTRY,
        current_view=current_view,
        steamid=dispatchers_steamid,
        options_view_toggle=False  # False = show "back" link
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Render options view
    # ─────────────────────────────────────────────────────────────────────────
    # BUG #2 Fix: Must pass widget_options to template!
    # Template loops over widget_options.items() to display key-value pairs.
    data_to_emit = module.template_render_hook(
        module,
        template=template_options,
        options_toggle=options_toggle,
        widget_options=module.options  # BUG #2: This was missing initially!
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


# ═══════════════════════════════════════════════════════════════════════════
# HANDLER: New/Updated Items (Granular Row Updates)
# ═══════════════════════════════════════════════════════════════════════════
def table_rows(*args, **kwargs):
    """
    DOM Callback Handler - Called when items are added or updated.
    
    Trigger: module_example_checkboxes/elements/{dataset}/{id} changes
    
    This handler performs GRANULAR updates:
    - Only updates/inserts the specific row that changed
    - Does NOT re-render the entire table
    - Sends individual <tr> elements to browser via send_data_to_client_hook
    
    The browser's data handler will:
    - Insert new rows if they don't exist
    - Update existing rows if they do exist
    - Use target_element.id to identify the row
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


# ═══════════════════════════════════════════════════════════════════════════
# HANDLER: Checkbox Selection Changes (Ultra-Granular Updates)
# ═══════════════════════════════════════════════════════════════════════════
def update_selection_status(*args, **kwargs):
    """
    DOM Callback Handler - Called when checkbox selection changes.
    
    Trigger: module_example_checkboxes/elements/{dataset}/{id}/selected_by changes
    
    This is the MOST GRANULAR update possible:
    - Only updates the <span> containing the checkbox control
    - Does NOT re-render the entire row
    - Does NOT re-render the entire table
    
    Flow:
    1. User clicks checkbox
    2. Browser sends select/deselect event to dom_management
    3. dom_management updates selected_by list in DOM
    4. DOM fires callback to THIS handler
    5. Handler calls dom_management.update_selection_status() helper
    6. Browser receives ONLY the updated checkbox <span>
    
    This ultra-granular approach ensures:
    - Minimal DOM manipulation
    - No flickering
    - Instant visual feedback
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
    
    # Update delete button status (enabled/disabled)
    update_delete_button_status(module, *args, **kwargs)


def update_delete_button_status(*args, **kwargs):
    """
    Updates the delete button status (enabled/disabled) based on selection count.
    
    Called after checkbox selection changes to enable/disable delete button.
    """
    module = args[0]

    module.dom_management.update_delete_button_status(
        *args, **kwargs,
        dom_element_root=module.dom_element_root,
        dom_element_select_root=module.dom_element_select_root,
        target_module=module,
        dom_action="delete_selected_dom_elements",
        dom_element_id={
            "id": "checkbox_table_widget_action_delete_button"
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# WIDGET REGISTRATION - Register widget with module system
# ═══════════════════════════════════════════════════════════════════════════
# This dict defines the widget and its handlers.
# The module system will:
# 1. Register main_widget as entry point (called on socket connect)
# 2. Register all handlers as DOM callbacks (called when DOM paths change)
#
# HANDLER PATHS use placeholders:
#   %steamid%            → Replaced with actual steamid
#   %dataset%            → Replaced with actual dataset name
#   %element_identifier% → Replaced with actual item id
widget_meta = {
    "description": "Example widget demonstrating checkbox table pattern with view toggles",
    "main_widget": select_view,  # Entry point: called on connect & disconnect
    
    "handlers": {
        # ─────────────────────────────────────────────────────────────────────
        # CRITICAL: View Toggle Handler
        # ─────────────────────────────────────────────────────────────────────
        # BUG #3 Fix: This handler was MISSING initially!
        # Without it, view changes are stored in DOM but widget is NOT re-rendered.
        # Result: View toggle only works after browser reload.
        #
        # This handler is triggered when:
        # - toggle_example_checkboxes_widget_view action calls set_current_view()
        # - set_current_view() updates: module_example_checkboxes/visibility/{steamid}/current_view
        # - DOM fires callback to this handler
        # - Handler calls select_view() → re-renders widget with new view
        "module_example_checkboxes/visibility/%steamid%/current_view":
            select_view,
        
        # ─────────────────────────────────────────────────────────────────────
        # Item Updates Handler (Granular Row Updates)
        # ─────────────────────────────────────────────────────────────────────
        # Called when new items are added or existing items updated.
        # Sends individual <tr> elements to browser (not entire table).
        "module_example_checkboxes/elements/%dataset%/%element_identifier%":
            table_rows,
        
        # ─────────────────────────────────────────────────────────────────────
        # Checkbox Selection Handler (Ultra-Granular Updates)
        # ─────────────────────────────────────────────────────────────────────
        # Called when selected_by list changes (checkbox clicked).
        # Sends ONLY the checkbox <span> to browser (not entire row).
        "module_example_checkboxes/elements/%dataset%/%element_identifier%/selected_by":
            update_selection_status,
    },
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_widget(widget_name, widget_meta)
