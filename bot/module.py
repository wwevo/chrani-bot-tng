from pprint import pp
from threading import Thread, Event
from time import time
from bot import started_modules_dict
from bot.mixins.telnet_trigger import TelnetTrigger
from bot.mixins.widget_renderer import WidgetRenderer
from bot.mixins.action import Action
from bot.mixins.template import Template

class Module(Thread, Action, TelnetTrigger, WidgetRenderer, Template):
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
        TelnetTrigger.__init__(self)
        WidgetRenderer.__init__(self)  # This calls CallbackHandler.__init__ via super()
        Template.__init__(self)
        Thread.__init__(self)

    def setup(self, provided_options=None):
        if provided_options is None:
            provided_options = {}

        self.options = self.default_options
        options_filename = "module_" + self.options['module_name'] + ".json"
        if isinstance(provided_options, dict):
            self.options.update(provided_options)
            print("found config for module {} in ./bot/options/{}".format(self.options['module_name'], options_filename))

        self.import_telnet_triggers()
        self.import_callback_handlers()
        self.import_actions()
        self.import_templates()
        self.name = self.options['module_name']

        return self

    @property
    def start(self):
        for required_module in self.required_modules:
            setattr(self, required_module[7:], started_modules_dict[required_module])

        setattr(self, self.name, self)  # add self to dynamic module list to unify calls from actions

        self.setDaemon(daemonic=True)

        # Call hook after daemon is set but BEFORE thread starts
        # This allows subclasses to start additional threads that should complete
        # before the main run() loop begins
        self.on_start()

        # Now start the thread (calls run() in new thread)
        Thread.start(self)
        WidgetRenderer.start(self)  # This also calls CallbackHandler.start() via inheritance

        return self

    def on_start(self):
        """
        Hook called after dependencies are injected but before thread starts.
        Override this in subclasses to perform initialization that needs to happen
        before the run() loop begins (e.g., starting additional threads).
        """
        pass

    def on_run_loop_iteration(self, loop_log, profile_start):
        """
        Hook called at the beginning of each run loop iteration, before periodic actions.
        Override this in subclasses to perform module-specific work on each iteration
        (e.g., reading from a telnet connection, processing queues).

        Args:
            loop_log: String for logging this iteration
            profile_start: Timestamp when this iteration started

        Returns:
            Updated loop_log string
        """
        return loop_log

    def run(self):
        """
        Default implementation of the periodic actions loop.
        Most modules can use this as-is. Override only if you need completely
        different behavior (which should be rare).
        """
        while not self.stopped.wait(self.next_cycle):
            loop_log = "{} - loop started | ".format(self.get_module_identifier())
            profile_start = time()

            # Call hook for module-specific iteration work
            loop_log = self.on_run_loop_iteration(loop_log, profile_start)

            # Execute periodic actions
            for action_id, action_meta in self.available_actions_dict.items():
                try:
                    if action_meta.get("parameters").get("enabled") and action_meta.get("parameters").get("periodic"):
                        self.trigger_action_hook(self, action_meta)
                        loop_log += "triggered action hook for {} | ".format(action_id)
                except:
                    loop_log += "{} is not using new metadata | ".format(action_id)

            self.last_execution_time = time() - profile_start
            self.next_cycle = int(self.run_observer_interval - self.last_execution_time)
            loop_log += "{} - loop took {} | ".format(self.get_module_identifier(), int(self.last_execution_time))
            # print(loop_log)

    def on_browser_widget_action(self, module, action_data, dispatchers_id=None):
        """ module-specific entry point for action events sent by the browser.
        Is triggered by the webservers browser_widget_action socket.io event """
        action_id = action_data.get("action")
        action_meta = self.available_actions_dict.get(action_id)
        action_meta["action_data"] = action_data

        print("browser action {} for widget {} in module {}".format(
            action_id, action_data.get("id"), action_data.get("widget_module")
        ))

        self.trigger_action_hook(module, action_meta, dispatchers_id=dispatchers_id)
