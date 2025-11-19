from bot import loaded_modules_dict
from os import path, pardir

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid=None):
    """
    Injects a raw telnet line directly into the telnet processing queue.

    This simulates receiving a line from the game server's telnet connection,
    triggering all normal trigger processing.

    Event data format:
    {
        'line': str  # The telnet line to inject (will be validated and processed)
    }
    """
    event_data[1]["action_identifier"] = action_name
    telnet_line = event_data[1].get("line", None)

    if telnet_line is None or len(telnet_line.strip()) == 0:
        event_data[1]["fail_reason"] = "no telnet line provided"
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    # Validate the line format (should look like a real telnet line)
    if not module.telnet.is_a_valid_line(telnet_line):
        # If not valid, still inject it but warn
        print(f"[Testing] WARNING: Injecting potentially invalid telnet line: {telnet_line[:100]}...")

    # Inject directly into the telnet processing queue
    module.telnet.telnet_lines_to_process.append(telnet_line)

    # Also store it in the valid lines for visibility
    module.telnet._store_valid_line(telnet_line)

    # Update DOM statistics
    current_count = module.dom.data.get(module.get_module_identifier(), {}).get("injection_count", 0)
    module.dom.data.upsert({
        module.get_module_identifier(): {
            "last_injected_line": telnet_line[:200],  # Store first 200 chars
            "injection_count": current_count + 1
        }
    })

    module.callback_success(callback_success, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    telnet_line = event_data[1].get("line", "")
    print(f"[Testing] Injected telnet line: {telnet_line[:100]}...")


def callback_fail(module, event_data, dispatchers_steamid):
    fail_reason = event_data[1].get("fail_reason", "unknown error")
    print(f"[Testing] Failed to inject telnet line: {fail_reason}")


action_meta = {
    "description": "Injects a raw telnet line for testing",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,  # We're injecting, not sending
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
