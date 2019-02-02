from os import path, listdir, pardir
from importlib import import_module
from threading import Thread


class Action(object):
    available_actions_dict = dict

    def __init__(self):
        self.available_actions_dict = {}

    def register_action(self, identifier, action_dict):
        self.available_actions_dict[identifier] = action_dict

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

    def manually_trigger_action(self, event_data):
        action_identifier = event_data[0]
        if action_identifier in self.available_actions_dict:
            status_message = "found requested action '{}'".format(action_identifier)

            server_is_online = self.dom.data.get("module_telnet", {}).get("server_is_online", False)
            action_requires_server_to_be_online = self.available_actions_dict[action_identifier].get(
                "requires_telnet_connection", False
            )
            if server_is_online is True or action_requires_server_to_be_online is not True:
                Thread(
                    target=self.available_actions_dict[action_identifier]["main_function"],
                    args=(self, event_data)
                ).start()
            else:
                status_message = "action '{}' requires an active telnet connection!".format(action_identifier)

        else:
            status_message = "could not find requested action '{}'".format(action_identifier)

        print(status_message)
