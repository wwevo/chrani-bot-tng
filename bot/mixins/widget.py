from os import path, listdir, pardir
from importlib import import_module


class Widget(object):
    available_widgets_dict = dict
    trigger_widget_hook = object
    trigger_widget_component_hook = object

    def __init__(self):
        self.available_widgets_dict = {}
        self.trigger_widget_hook = self.trigger_widget
        self.trigger_widget_component_hook = self.trigger_widget_component

    def trigger_widget(self, module, dispatchers_steamid=None):
        if isinstance(self.available_widgets_dict, dict) and len(self.available_widgets_dict) >= 1:
            for name, widget in self.available_widgets_dict.items():
                if widget["main_widget"] is not None:
                    widget["main_widget"](self, dispatchers_steamid=dispatchers_steamid)

    def trigger_widget_component(self, module, event_data, dispatchers_steamid=None):
        if event_data[0] == 'request_table_row':
            """ if the JS-frontend receives an update request for an element not yet present (player-table-row,
            whitelist-table-row, such things) it will request the row """
            widget = self.available_widgets_dict[event_data[1]["widget"]]
            if widget["component_widget"] is not None:
                widget["component_widget"](self, event_data, dispatchers_steamid=dispatchers_steamid)

    def on_socket_connect(self, dispatchers_steamid):
        self.trigger_widget_hook(self, dispatchers_steamid=dispatchers_steamid)

    def on_socket_disconnect(self, dispatchers_steamid):
        self.trigger_widget_hook(self, dispatchers_steamid=dispatchers_steamid)

    def on_socket_event(self, event_data, dispatchers_steamid):
        self.trigger_widget_component_hook(self, event_data, dispatchers_steamid=dispatchers_steamid)

    def start(self):
        if isinstance(self.available_widgets_dict, dict) and len(self.available_widgets_dict) >= 1:
            for name, widget in self.available_widgets_dict.items():
                for trigger, handler in widget["handlers"].items():
                    self.dom.data.register_callback(self, trigger, handler)
                    # print(trigger, handler)

    def register_widget(self, identifier, widget_dict):
        self.available_widgets_dict[identifier] = widget_dict

    def import_widgets(self):
        modules_root_dir = path.join(path.dirname(path.abspath(__file__)), pardir, "modules")

        module_widgets_root_dir = path.join(modules_root_dir, self.options['module_name'], "widgets")
        try:
            for module_widget in listdir(module_widgets_root_dir):
                if module_widget == 'common.py' or module_widget == '__init__.py' or module_widget[-3:] != '.py':
                    continue
                import_module("bot.modules." + self.options['module_name'] + ".widgets." + module_widget[:-3])
        except FileNotFoundError as error:
            # module does not have widgets
            pass
