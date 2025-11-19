from bot import loaded_modules_dict
from os import path, pardir, listdir
import json

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    """
    Loads and executes a test scenario from the scenarios directory.

    Event data format:
    {
        'scenario': str  # Scenario name (e.g., "basic", "stress", "permissions")
    }
    """
    event_data[1]["action_identifier"] = action_name

    scenario_name = event_data[1].get("scenario", None)
    if scenario_name is None:
        event_data[1]["fail_reason"] = "no scenario name provided"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    # Get scenarios directory
    module_dir = path.dirname(path.abspath(path.join(__file__, pardir, pardir)))
    scenarios_dir = path.join(module_dir, "scenarios")
    scenario_file = path.join(scenarios_dir, f"{scenario_name}.json")

    # Check if scenario exists
    if not path.exists(scenario_file):
        event_data[1]["fail_reason"] = f"scenario '{scenario_name}' not found"
        event_data[1]["available_scenarios"] = get_available_scenarios(scenarios_dir)
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    # Load scenario JSON
    try:
        with open(scenario_file, 'r') as f:
            scenario_data = json.load(f)
    except json.JSONDecodeError as e:
        event_data[1]["fail_reason"] = f"invalid JSON in scenario file: {str(e)}"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    # Execute all actions in the scenario
    actions_executed = 0
    for action_def in scenario_data.get("actions", []):
        action_name_to_call = action_def.get("action")
        action_data = action_def.get("data", {})

        # Trigger the action
        action_event_data = [action_name_to_call, action_data]
        module.trigger_action_hook(module, event_data=action_event_data)
        actions_executed += 1

    # Update DOM with loaded scenario
    scenarios_loaded = module.dom.data.get(module.get_module_identifier(), {}).get("scenarios_loaded", [])
    scenarios_loaded.append({
        "name": scenario_name,
        "description": scenario_data.get("description", ""),
        "actions_count": actions_executed
    })

    module.dom.data.upsert({
        module.get_module_identifier(): {
            "scenarios_loaded": scenarios_loaded
        }
    })

    event_data[1]["scenario_data"] = scenario_data
    event_data[1]["actions_executed"] = actions_executed

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def get_available_scenarios(scenarios_dir):
    """Returns list of available scenario names."""
    if not path.exists(scenarios_dir):
        return []

    scenarios = []
    for filename in listdir(scenarios_dir):
        if filename.endswith('.json'):
            scenarios.append(filename[:-5])  # Remove .json extension
    return scenarios


def callback_success(module, event_data, dispatchers_steamid, match=None):
    scenario_name = event_data[1].get("scenario", "unknown")
    actions_count = event_data[1].get("actions_executed", 0)
    scenario_desc = event_data[1].get("scenario_data", {}).get("description", "")
    print(f"[Testing] Loaded scenario '{scenario_name}': {scenario_desc}")
    print(f"[Testing] Executed {actions_count} actions")


def callback_fail(module, event_data, dispatchers_steamid):
    fail_reason = event_data[1].get("fail_reason", "unknown error")
    available = event_data[1].get("available_scenarios", [])
    print(f"[Testing] Failed to load scenario: {fail_reason}")
    if available:
        print(f"[Testing] Available scenarios: {', '.join(available)}")


action_meta = {
    "description": "Loads and executes a test scenario from JSON file",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
