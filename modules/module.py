import jinja2
from os import path
from threading import Thread, Event
from modules import started_modules_dict


class Module(Thread):
    """ This class may ONLY be used to extend a module, it is not meant to be instantiated on it's own """
    templates = object
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

        modules_root_dir = path.dirname(path.abspath(__file__))
        modules_template_dir = path.join(modules_root_dir, self.options['module_name'], 'templates')

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

    def on_socket_connect(self, sid):
        pass

    def on_socket_event(self, event_data, dispatchers_steamid):
        print("module '{}' received event {} from {}".format(
            self.options['module_name'], event_data, dispatchers_steamid
        ))
