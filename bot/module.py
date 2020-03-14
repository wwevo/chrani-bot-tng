from threading import Thread, Event
from bot import started_modules_dict
from bot.mixins.trigger import Trigger
from bot.mixins.action import Action
from bot.mixins.template import Template
from bot.mixins.widget import Widget


class Module(Thread, Action, Trigger, Template, Widget):
    """ This class may ONLY be used to extend a module, it is not meant to be instantiated on it's own """
    options = dict
    stopped = object

    run_observer_interval = int
    run_observer_interval_idle = int

    last_execution_time = float

    def __init__(self):
        if type(self) is Module:
            raise NotImplementedError("You may not instantiate this class on it's own")

        self.stopped = Event()
        Action.__init__(self)
        Trigger.__init__(self)
        Template.__init__(self)
        Widget.__init__(self)
        Thread.__init__(self)

    def setup(self, provided_options=dict):
        self.options = self.default_options
        options_filename = "module_" + self.options['module_name'] + ".json"
        if isinstance(provided_options, dict):
            self.options.update(provided_options)
            print(
                (
                    "{module_name}: provided options have been set ({options_filename})"
                ).format(
                    module_name=self.options['module_name'],
                    options_filename=options_filename
                )
            )
        else:
            print(
                (
                    "{module_name}: no options-file provided (was looking for \"{options_filename}\"), "
                    "default values are used"
                ).format(
                    module_name=self.default_options["module_name"],
                    options_filename=options_filename
                )
            )

        self.import_triggers()
        self.import_actions()
        self.import_templates()
        self.import_widgets()
        self.name = self.options['module_name']
        return self

    def start(self):
        for required_module in self.required_modules:
            setattr(self, required_module[7:], started_modules_dict[required_module])
        setattr(self, self.name, self)  # add self to dynamic module list to unify calls from actions

        self.setDaemon(daemonic=True)
        Thread.start(self)
        Widget.start(self)
        Trigger.start(self)

        return self

    def on_socket_connect(self, dispatchers_steamid):
        # print("'{}' connected to module {}".format(
        #     dispatchers_steamid, self.options['module_name']
        # ))
        Widget.on_socket_connect(self, dispatchers_steamid)

    def on_socket_disconnect(self, dispatchers_steamid):
        # print("'{}' disconnected from module {}".format(
        #     dispatchers_steamid, self.options['module_name']
        # ))
        Widget.on_socket_disconnect(self, dispatchers_steamid)

    def on_socket_event(self, event_data, dispatchers_steamid):
        self.trigger_action_hook(self, event_data=event_data, dispatchers_steamid=dispatchers_steamid)
        self.emit_event_status(self, event_data, dispatchers_steamid)

        Widget.on_socket_event(self, event_data, dispatchers_steamid)

    def emit_event_status(self, module, event_data, recipient_steamid, status=None):
        # recipient_steamid can be None, "all" or [list_of_steamid's]
        if recipient_steamid is not None and status is not None:
            recipient_steamid = [recipient_steamid]

            self.webserver.emit_event_status(module, event_data, recipient_steamid, status)

    @staticmethod
    def callback_success(callback, module, event_data, dispatchers_steamid, match=None):
        event_data[1]["status"] = "success"
        module.emit_event_status(module, event_data, dispatchers_steamid, event_data[1])
        callback(module, event_data, dispatchers_steamid, match)

    @staticmethod
    def callback_fail(callback, module, event_data, dispatchers_steamid):
        event_data[1]["status"] = "fail"
        print("FAILED ACTION:", module.getName(), event_data)
        module.emit_event_status(module, event_data, dispatchers_steamid, event_data[1])
        callback(module, event_data, dispatchers_steamid)
