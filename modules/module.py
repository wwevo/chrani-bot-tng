from threading import Thread, Event
from modules import started_modules_dict


class Module(Thread):
    """ This class may ONLY be used to extend a module, it is not meant to be instantiated on it's own """
    options = dict
    stopped = object

    run_observer_interval = int
    last_execution_time = float

    def __init__(self):
        if type(self) is Module:
            raise NotImplementedError("You may not instantiate this class on it's own")

        self.stopped = Event()
        Thread.__init__(self)

    def setup(self, options=dict):
        self.options = self.default_options
        if isinstance(options, dict):
            self.options.update(options)
            print("{}: provided options have been set".format(self.options['module_name']))
        else:
            print("{}: no options provided, default values are used".format(self.default_options["module_name"]))

        self.name = self.options['module_name']
        return self

    def start(self):
        for required_module in self.required_modules:
            setattr(self, required_module[7:], started_modules_dict[required_module])

        self.setDaemon(daemonic=True)
        Thread.start(self)
        return self
