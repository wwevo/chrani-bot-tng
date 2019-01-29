from threading import Thread, Event
from module import started_modules_dict
from .trigger import Trigger
from .action import Action
from .template import Template


class Module(Thread, Action, Trigger, Template):
    """ This class may ONLY be used to extend a module, it is not meant to be instantiated on it's own """
    # we are importing Action and Trigger class to make them available. requires actions and triggers to be there ^^
    options = dict
    stopped = object

    run_observer_interval = int
    last_execution_time = float

    available_triggers_dict = dict
    available_actions_dict = dict

    def __init__(self):
        if type(self) is Module:
            raise NotImplementedError("You may not instantiate this class on it's own")

        self.stopped = Event()
        self.available_triggers_dict = {}
        self.available_actions_dict = {}
        Action.__init__(self)
        Trigger.__init__(self)
        Thread.__init__(self)

    def setup(self, options=dict):
        self.options = self.default_options
        if isinstance(options, dict):
            self.options.update(options)
            print("{}: provided options have been set".format(self.options['module_name']))
        else:
            print("{}: no options provided, default values are used".format(self.default_options["module_name"]))

        self.import_triggers()
        self.import_actions()
        self.import_templates()

        self.name = self.options['module_name']
        return self

    def start(self):
        for required_module in self.required_modules:
            setattr(self, required_module[7:], started_modules_dict[required_module])
        setattr(self, self.name, self)  # add self to dnamic module list to unify calls from actions

        self.setDaemon(daemonic=True)
        Thread.start(self)
        return self

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

        if dispatchers_steamid is not None:
            # we don't need to dispatch a status if there's no user doing the call, unless it's a broadcast!
            self.emit_event_status(event_data, dispatchers_steamid, status)

    def emit_event_status(self, event_data, recipient_steamid, status):
        # recipient_steamid can be None, all or [list_of_steamid's]
        if recipient_steamid is None:
            return

        action_identifier = event_data[0]
        print("module '{}' sent status '{}' for '{}' to {}".format(
            self.options['module_name'], status, action_identifier, recipient_steamid
        ))
        self.webserver.send_data_to_client(
            event_data,
            data_type="status_message",
            clients=[recipient_steamid],
            status=status
        )
