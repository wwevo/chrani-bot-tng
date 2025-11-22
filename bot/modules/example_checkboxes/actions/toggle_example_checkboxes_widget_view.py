"""
═══════════════════════════════════════════════════════════════════════════════
VIEW TOGGLE ACTION - How to implement view switching
═══════════════════════════════════════════════════════════════════════════════

This action demonstrates the standard pattern for view toggle actions.

HOW VIEW TOGGLES WORK:
───────────────────────────────────────────────────────────────────────────────
1. User clicks toggle link in template (e.g., "options" or "back")
2. Browser sends socket.emit('widget_event', ['example_checkboxes', 
   ['toggle_example_checkboxes_widget_view', {'action': 'show_options'}]])
3. This action is called
4. Action calls module.set_current_view(steamid, {'current_view': 'options'})
5. set_current_view() updates DOM: module_example_checkboxes/visibility/{steamid}/current_view
6. DOM fires callback to visibility handler (registered in checkbox_widget.py)
7. Handler calls select_view() → re-renders widget with new view

IMPORTANT: Widget MUST have visibility handler registered!
See checkbox_widget.py line ~509 for handler registration.
Without it, view changes work but require browser reload (BUG #3).
"""

from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    """
    Toggles between different views in the example checkboxes widget.

    Required options:
    - action: View to show ("show_options" or "show_frontend")
    
    This action:
    - Validates the action parameter
    - Maps action to view name (show_options → "options")
    - Calls set_current_view() to update DOM
    - DOM callback triggers widget re-render (if handler registered!)
    """
    action = event_data[1].get("action", None)
    event_data[1]["action_identifier"] = action_name
    event_data[1]["fail_reason"] = ""

    if action == "show_options":
        current_view = "options"
    elif action == "show_frontend":
        current_view = "frontend"
    else:
        event_data[1]["fail_reason"] = "invalid action parameter"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    module.set_current_view(dispatchers_steamid, {
        "current_view": current_view
    })
    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    pass


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "Shows information about Example Checkboxes",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
