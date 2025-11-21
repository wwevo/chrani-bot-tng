"""
EXAMPLE MODULE: Checkbox Table Widget

This module demonstrates how to create a table with selectable checkboxes
following the bot's reactive architecture pattern.

Key Concepts Demonstrated:
1. DOM structure with elements under {module}/elements/{dataset}/{id}
2. Checkbox selection using dom_management.get_selection_dom_element()
3. Reactive updates via DOM callbacks
4. Proper handler registration for selection changes
5. Component-based template rendering

This is a minimal working example - use it as a template for new modules!
"""

from bot.module import Module
from bot import loaded_modules_dict


class ExampleCheckboxes(Module):
    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
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

    @staticmethod
    def get_module_identifier():
        return "module_example_checkboxes"

    def setup(self, options=dict):
        Module.setup(self, options)

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
