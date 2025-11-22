"""
═══════════════════════════════════════════════════════════════════════════════
TUTORIAL MODULE: Checkbox Table Widget with View Toggle
═══════════════════════════════════════════════════════════════════════════════

This module is a COMPLETE REFERENCE IMPLEMENTATION for:
✓ Checkbox tables with selectable rows
✓ Reactive view toggles (Options ↔ Frontend)
✓ Granular DOM updates (only changed elements)
✓ Proper handler registration

Use this as a template for new modules!


KEY FILES TO STUDY:
───────────────────────────────────────────────────────────────────────────────
1. widgets/checkbox_widget.py
   → Main widget logic with extensive tutorial comments
   → View routing, rendering, handlers
   → Documents all 4 bugfixes

2. actions/toggle_example_checkboxes_widget_view.py
   → View toggle action (Options ↔ Frontend)
   → Shows how to use set_current_view()

3. templates/checkbox_widget/*.html
   → Micro-templates for granular updates
   → control_view_menu.html shows toggle link pattern


KEY CONCEPTS:
───────────────────────────────────────────────────────────────────────────────
1. DOM Structure: {module}/elements/{dataset}/{id}
   → Must be called "elements" (dom_management hardcodes this)
   → Each item needs: id, owner, identifier, dataset, selected_by

2. Checkbox Selection:
   → Uses dom_management.get_selection_dom_element()
   → Browser → dom_management/select → DOM update → callback → render

3. View Toggle:
   → Requires visibility handler: {module}/visibility/%steamid%/current_view
   → Action calls set_current_view() → DOM update → handler → re-render

4. Granular Updates:
   → Row updates: Send individual <tr> elements
   → Checkbox updates: Send ONLY <span> with checkbox control
   → No full table re-renders unless necessary
"""

from bot.module import Module
from bot import loaded_modules_dict


class ExampleCheckboxes(Module):
    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "dom_element_root": [],
            "dom_element_select_root": ["selected_by"],
        })

        setattr(self, "required_modules", [
            "module_dom",
            "module_dom_management",
            "module_webserver"
        ])

        self.next_cycle = 0
        self.all_available_actions_dict = {}
        self.all_available_widgets_dict = {}
        Module.__init__(self)

    def setup(self, options=dict):
        Module.setup(self, options)
        
        self.dom_element_root = self.options.get(
            "dom_element_root", self.default_options.get("dom_element_root", None)
        )
        self.dom_element_select_root = self.options.get(
            "dom_element_select_root", self.default_options.get("dom_element_select_root", None)
        )

    @staticmethod
    def get_module_identifier():
        return "module_example_checkboxes"

    def start(self):
        """Initialize some example data in the DOM"""
        Module.start(self)

        # Create some example elements
        example_data = {
            "example_dataset": {
                "item_001": {
                    "id": "item_001",
                    "owner": "item_001",
                    "identifier": "item_001",
                    "name": "Example Item 1",
                    "description": "First example item",
                    "dataset": "example_dataset",
                    "selected_by": []
                },
                "item_002": {
                    "id": "item_002",
                    "owner": "item_002",
                    "identifier": "item_002",
                    "name": "Example Item 2",
                    "description": "Second example item",
                    "dataset": "example_dataset",
                    "selected_by": []
                },
                "item_003": {
                    "id": "item_003",
                    "owner": "item_003",
                    "identifier": "item_003",
                    "name": "Example Item 3",
                    "description": "Third example item",
                    "dataset": "example_dataset",
                    "selected_by": []
                }
            }
        }

        # Store in DOM under module_example_checkboxes/elements
        self.dom.data.upsert({
            self.get_module_identifier(): {
                "elements": example_data
            }
        })

    def run(self):
        pass


loaded_modules_dict[ExampleCheckboxes().get_module_identifier()] = ExampleCheckboxes()
