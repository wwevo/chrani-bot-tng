from bot import loaded_modules_dict
from os import path, pardir
from time import sleep, time
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def main_function(module, event_data, dispatchers_steamid):
    timeout = 3  # [seconds]
    timeout_start = time()

    cancel_shutdown = event_data[1].get("cancel", False)
    force_shutdown = event_data[1].get("force", False)
    alert_admin = event_data[1].get("alert_admin", False)

    if cancel_shutdown == 1:
        module.dom.data.upsert({
            module.get_module_identifier(): {
                "cancel_shutdown": True
            }
        })

    if force_shutdown == 1:
        module.dom.data.upsert({
            module.get_module_identifier(): {
                "force_shutdown": True
            }
        })

    if alert_admin == 1:
        module.webserver.send_data_to_client(
            event_data=event_data,
            status="admin contacted! (well, not really)",
            data_type="alert_message",
            clients=[dispatchers_steamid],
        )

    shutdown_in_seconds = module.dom.data.get(module.get_module_identifier()).get("shutdown_in_seconds", None)
    if shutdown_in_seconds is None and not alert_admin:  # should only be none if no shutdown task is running!
        shutdown_timeout_start = time()
        try:
            shutdown_timeout = int(event_data[1]["timer"])
        except Exception as error:
            shutdown_timeout = 30
            print(type(error))

        shutdown_canceled = False
        while time() < shutdown_timeout_start + shutdown_timeout:
            if module.dom.data.get(module.get_module_identifier()).get("cancel_shutdown", False):
                shutdown_canceled = True
                break

            if module.dom.data.get(module.get_module_identifier()).get("force_shutdown", False):
                break

            module.dom.data.upsert({
                module.get_module_identifier(): {
                    "shutdown_in_seconds": int(shutdown_timeout - (time() - shutdown_timeout_start))
                }
            })
            module.update_gameserver_status_widget_frontend()
            sleep(1)

        module.dom.data.upsert({
            module.get_module_identifier(): {
                "shutdown_in_seconds": None,
                "cancel_shutdown": False,
                "force_shutdown": False
            }
        })

        if not shutdown_canceled:
            module.telnet.add_telnet_command_to_queue("shutdown")
            poll_is_finished = False
            regex = (
                r"(?P<datetime>.+?)\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s.*\s"
                r"INF Disconnect.*"
            )

            while not poll_is_finished and (time() < timeout_start + timeout):
                sleep(0.25)
                match = False
                for match in re.finditer(regex, module.telnet.telnet_buffer):
                    poll_is_finished = True

                if match:
                    callback_success(module, event_data, dispatchers_steamid, match)
                    return

        module.update_gameserver_status_widget_frontend()

    callback_fail(module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match):
    module.emit_event_status(event_data, dispatchers_steamid, "success")


def callback_fail(module, event_data, dispatchers_steamid):
    module.emit_event_status(event_data, dispatchers_steamid, "fail")


action_meta = {
    "description": "shuts down the server",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
