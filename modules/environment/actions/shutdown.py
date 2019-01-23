from modules import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid, **kwargs):
    timeout = 3  # [seconds]
    timeout_start = time()

    try:
        cancel_shutdown = event_data[1]["cancel"]
    except Exception as error:
        cancel_shutdown = False
        print(type(error))

    if cancel_shutdown == 1:
        module.dom.upsert({
            module.get_module_identifier(): {
                "cancel_shutdown": True
            }
        })

    shutdown_in_seconds = module.dom.data.get(module.get_module_identifier()).get("shutdown_in_seconds", None)
    if shutdown_in_seconds is None:
        shutdown_timeout_start = time()
        shutdown_timeout = int(event_data[1]["timer"])
        shutdown_canceled = False
        while time() < shutdown_timeout_start + shutdown_timeout:
            if module.dom.data.get(module.get_module_identifier()).get("cancel_shutdown", False):
                shutdown_canceled = True
                break

            module.dom.upsert({
                module.get_module_identifier(): {
                    "shutdown_in_seconds": int(shutdown_timeout - (time() - shutdown_timeout_start))
                }
            })
            module.update_status_widget()
            sleep(1)

        module.dom.upsert({
            module.get_module_identifier(): {
                "shutdown_in_seconds": None,
                "cancel_shutdown": False
            }
        })
        if not shutdown_canceled:
            module.telnet.add_telnet_command_to_queue("shutdown")
            poll_is_finished = False
            while not poll_is_finished and (time() < timeout_start + timeout):
                match = False
                for match in re.finditer(r"^(?P<datetime>.+?) (?P<stardate>.+?) INF Disconnect.*$", module.telnet.telnet_buffer):
                    poll_is_finished = True

                if match:
                    callback_success(module, event_data, dispatchers_steamid, match, **kwargs)
                    return

                sleep(0.5)
        module.update_status_widget()

    callback_fail(module, event_data, dispatchers_steamid, **kwargs)


def callback_success(module, event_data, dispatchers_steamid, match, **kwargs):
    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid, **kwargs):
    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "shuts down the server",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
