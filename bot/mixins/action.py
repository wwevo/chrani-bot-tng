from os import path, listdir, pardir
from importlib import import_module
from threading import Thread
from bot import loaded_modules_dict
from time import sleep
import string
import random


class Action(object):
    available_actions_dict = dict
    trigger_action_hook = object

    def __init__(self):
        self.available_actions_dict = {}
        self.trigger_action_hook = self.trigger_action

    def register_action(self, identifier, action_dict):
        self.available_actions_dict[identifier] = action_dict

    def enable_action(self, identifier):
        self.available_actions_dict[identifier]["enabled"] = True

    def disable_action(self, identifier):
        self.available_actions_dict[identifier]["enabled"] = False

    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    @staticmethod
    def get_all_available_actions_dict():
        all_available_actions_dict = {}
        for loaded_module_identifier, loaded_module in loaded_modules_dict.items():
            if len(loaded_module.available_actions_dict) >= 1:
                all_available_actions_dict[loaded_module_identifier] = loaded_module.available_actions_dict

        return all_available_actions_dict

    def import_actions(self):
        modules_root_dir = path.join(path.dirname(path.abspath(__file__)), pardir, "modules")

        module_actions_root_dir = path.join(modules_root_dir, self.options['module_name'], "actions")
        try:
            for module_action in listdir(module_actions_root_dir):
                if module_action == 'common.py' or module_action == '__init__.py' or module_action[-3:] != '.py':
                    continue
                import_module("bot.modules." + self.options['module_name'] + ".actions." + module_action[:-3])
        except FileNotFoundError as error:
            # module does not have actions
            pass

    @staticmethod
    def trigger_action(target_module, event_data=None, dispatchers_steamid=None):
        if event_data is None:
            event_data = []
        action_identifier = event_data[0]
        if action_identifier in target_module.available_actions_dict:
            server_is_online = target_module.dom.data.get("module_telnet", {}).get("server_is_online", False)
            active_action = target_module.available_actions_dict[action_identifier]
            action_requires_server_to_be_online = active_action.get(
                "requires_telnet_connection", False
            )
            action_is_enabled = active_action.get("enabled", False)
            user_has_permission = event_data[1].get("has_permission", None)
            # permission is None = no status has been set, so it's allowed (default)
            # permission is True = Permission has been set by some other process
            # permission is False = permission has not been granted by any module

            if dispatchers_steamid is not None:
                # none would be a system-call
                pass

            if action_is_enabled:
                event_data[1]["module"] = target_module.getName()
                event_data[1]["uuid4"] = target_module.id_generator(22)
                if server_is_online is True or action_requires_server_to_be_online is not True:
                    if any([
                        user_has_permission is None,
                        user_has_permission is True
                    ]):
                        Thread(
                            target=active_action.get("main_function"),
                            args=(target_module, event_data, dispatchers_steamid)
                        ).start()
                    else:
                        # in case we don't have permission, we call the fail callback. it then can determine what to do
                        # next
                        fail_callback = active_action.get("callback_fail")
                        Thread(
                            target=target_module.callback_fail(
                                fail_callback,
                                target_module,
                                event_data,
                                dispatchers_steamid
                            ),
                            args=(target_module, event_data, dispatchers_steamid)
                        ).start()
                else:
                    try:
                        skip_it_callback = active_action.get("skip_it")
                        Thread(
                            target=skip_it_callback,
                            args=(target_module, event_data)
                        ).start()
                    except KeyError:
                        pass
