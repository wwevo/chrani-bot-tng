from bot import loaded_modules_dict
from os import path, pardir
from time import time, sleep
import random
import re

module_name = path.basename(path.normpath(path.join(path.abspath(__file__), pardir, pardir)))
action_name = path.basename(path.abspath(__file__))[:-3]


def kill_entity(module, event_data, dispatchers_steamid=None):
    timeout = 8  # [seconds]
    timeout_start = time()

    entity_to_be_killed = event_data[1].get("entity_id", None)

    command = "kill {}".format(entity_to_be_killed)
    module.telnet.add_telnet_command_to_queue(command)
    poll_is_finished = False
    regex = (
        r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s(?P<stardate>[-+]?\d*\.\d+|\d+)\s"
        r"INF\sEntity\s(?P<zombie_name>.*)\s" + str(entity_to_be_killed) + r"\skilled"
    )
    while not poll_is_finished and (time() < timeout_start + timeout):
        sleep(0.25)
        match = False
        for match in re.finditer(regex, module.telnet.telnet_buffer, re.DOTALL):
            poll_is_finished = True

        if match:
            return match

    return False


def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get("action", None)
    dataset = event_data[1].get("dataset")
    entity_id = event_data[1].get("entity_id")
    entity_name = event_data[1].get("entity_name")

    if action is not None:
        if action == "kill":
            match = kill_entity(module, event_data, dispatchers_steamid)
            print(entity_name, action, match)
            if match is not False:
                if entity_name == "zombieScreamer":
                    module.callback_success(callback_success, module, event_data, dispatchers_steamid, match)

    module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)


def callback_success(module, event_data, dispatchers_steamid, match=None):
    action = event_data[1].get("action", None)
    entity_id = event_data[1].get("entity_id")
    entity_name = event_data[1].get("entity_name")

    if all([
        action is not None
    ]):
        if entity_name == "zombieScreamer":
            possible_maybes = [
                "hopefully",
                "probably dead, yes!",
                "i think",
                "i'm almost certain",
                "yeah. definitely!!"
            ]
            event_data = ['say_to_all', {
                'message': '[CCFFCC]Screamer ([FFFFFF]{entity_id}[CCFFCC]) killed[-], [FFFFFF]{maybe}[-]...'.format(
                    entity_id=entity_id,
                    maybe=random.choice(possible_maybes)
                )
            }]
            module.trigger_action_hook(module, event_data=event_data)
        else:
            event_data = ['say_to_all', {
                'message': '[CCFFCC]entity ([FFFFFF]{entity_id}[CCFFCC]) killed[-]'.format(
                    entity_id=entity_id
                )
            }]
            module.trigger_action_hook(module, event_data=event_data)


def callback_fail(module, event_data, dispatchers_steamid):
    pass


action_meta = {
    "description": "manages entity entries",
    "main_function": main_function,
    "callback_success": callback_success,
    "callback_fail": callback_fail,
    "requires_telnet_connection": False,
    "enabled": True
}

loaded_modules_dict["module_" + module_name].register_action(action_name, action_meta)
