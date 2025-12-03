from os import path, listdir, pardir
from importlib import import_module
from threading import Thread
from bot import loaded_modules_dict
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
        self.available_actions_dict[identifier]["parameters"]["enabled"] = True

    def disable_action(self, identifier):
        self.available_actions_dict[identifier]["parameters"]["enabled"] = False

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

    def callback_success(self, callback, action_meta, dispatchers_id, match=None):
        disable_after_success = action_meta.get("parameters").get("disable_after_success")
        if disable_after_success:
            print("disabled {} action {} after one successful run".format(
                self.get_module_identifier(), action_meta.get("id")
            ))
            self.disable_action(action_meta.get("id"))

        callback(self, action_meta, dispatchers_id, match)

    def callback_skip(self, callback, action_meta, dispatchers_id):
        callback(self, action_meta, dispatchers_id)

    def callback_fail(self, callback, action_meta, dispatchers_id):
        callback(self, action_meta, dispatchers_id)


    def trigger_action(self, target_module, action_meta, dispatchers_id=None):
        action_id = action_meta.get("id")
        if not action_id:
            return

        if action_meta.get("id") in target_module.available_actions_dict:
            action_is_enabled = action_meta.get("parameters").get("enabled", False)
            if action_is_enabled:
                server_is_online = target_module.dom.data.get("module_telnet", {}).get("server_is_online", False)
                action_requires_server_to_be_online = action_meta.get("parameters").get(
                    "requires_telnet_connection"
                )
                user_has_permission = action_meta.get("has_permission", None)
                # permission is None = no status has been set, so it's allowed (default)
                # permission is True = Permission has been set by some other process
                # permission is False = permission has not been granted by any module

                if dispatchers_id is not None:
                    # none would be a system-call
                    pass

                if server_is_online is True or action_requires_server_to_be_online is not True:
                    if any([
                        user_has_permission is None,
                        user_has_permission is True
                    ]):
                        Thread(
                            target=action_meta.get("main_function"),
                            args=(target_module, action_meta, dispatchers_id)
                        ).start()
                    else:
                        # in case we don't have permission, we call the fail callback. it then can determine what to do
                        # next
                        skip_callback = action_meta.get("callbacks").get("callback_skip")
                        Thread(
                            target=target_module.callback_skip(
                                skip_callback,
                                target_module,
                                action_meta,
                                dispatchers_id
                            ),
                            args=(target_module, action_meta, dispatchers_id)
                        ).start()
                else:
                    skip_callback = action_meta.get("callbacks").get("callback_skip")
                    Thread(
                        target=target_module.callback_skip(
                            skip_callback,
                            target_module,
                            action_meta,
                            dispatchers_id
                        ),
                        args=(target_module, action_meta, dispatchers_id)
                    ).start()
