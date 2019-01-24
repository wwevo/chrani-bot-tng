import jinja2
from os import path, listdir
from importlib import import_module
from threading import Thread, Event
from modules import started_modules_dict


class Module(Thread):
    """ This class may ONLY be used to extend a module, it is not meant to be instantiated on it's own """
    templates = object
    options = dict
    stopped = object

    run_observer_interval = int
    last_execution_time = float

    available_actions_dict = dict

    def __init__(self):
        if type(self) is Module:
            raise NotImplementedError("You may not instantiate this class on it's own")

        self.available_actions_dict = {}
        self.stopped = Event()
        Thread.__init__(self)

    def setup(self, options=dict):
        self.options = self.default_options
        if isinstance(options, dict):
            self.options.update(options)
            print("{}: provided options have been set".format(self.options['module_name']))
        else:
            print("{}: no options provided, default values are used".format(self.default_options["module_name"]))

        modules_root_dir = path.dirname(path.abspath(__file__))
        modules_template_dir = path.join(modules_root_dir, self.options['module_name'], 'templates')

        module_actions_root_dir = path.join(modules_root_dir, self.options['module_name'], "actions")
        try:
            for module_action in listdir(module_actions_root_dir):
                if module_action == 'common.py' or module_action == '__init__.py' or module_action[-3:] != '.py':
                    continue
                import_module("modules." + self.options['module_name'] + ".actions." + module_action[:-3])
        except FileNotFoundError as error:
            # module does not have actions
            pass

        file_loader = jinja2.FileSystemLoader(modules_template_dir)
        self.templates = jinja2.Environment(loader=file_loader)

        self.name = self.options['module_name']
        return self

    def start(self):
        for required_module in self.required_modules:
            setattr(self, required_module[7:], started_modules_dict[required_module])

        self.setDaemon(daemonic=True)
        Thread.start(self)
        return self

    def register_action(self, identifier, action_dict):
        self.available_actions_dict[identifier] = action_dict

    def on_socket_connect(self, sid):
        print("'{}' connected to module {}".format(
            sid, self.options['module_name']
        ))

    def on_socket_disconnect(self, sid):
        print("'{}' disconnected from module {}".format(
            sid, self.options['module_name']
        ))

    def on_socket_event(self, event_data, dispatchers_steamid):
        action_identifier = event_data[0]
        print("module '{}' received event '{}' from {}".format(
            self.options['module_name'], action_identifier, dispatchers_steamid
        ))

        if action_identifier in self.available_actions_dict:
            status = "found requested action '{}'".format(action_identifier)
            Thread(
                target=self.available_actions_dict[action_identifier]["main_function"],
                args=(self, event_data, dispatchers_steamid)
            ).start()
        else:
            status = "could not find requested action '{}'".format(action_identifier)

        self.emit_event_status(event_data, dispatchers_steamid, status)

    def manually_trigger_event(self, event_data):
        action_identifier = event_data[0]
        if action_identifier in self.available_actions_dict:
            status = "found requested action '{}'".format(action_identifier)
            Thread(
                target=self.available_actions_dict[action_identifier]["main_function"],
                args=(self, event_data)
            ).start()
        else:
            status = "could not find requested action '{}'".format(action_identifier)

        print(status)

    def emit_event_status(self, event_data, recipient_steamid, status):
        action_identifier = event_data[0]
        print("module '{}' sent status '{}' for '{}' to {}".format(
            self.options['module_name'], status, action_identifier, recipient_steamid
        ))
        self.webserver.send_data_to_client(
            event_data,
            data_type="status_message",
            clients=None if recipient_steamid is None else [recipient_steamid],
            status=status
        )
