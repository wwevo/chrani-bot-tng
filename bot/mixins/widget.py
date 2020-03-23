from os import path, listdir, pardir
from importlib import import_module
from bot import loaded_modules_dict


class Widget(object):
    available_widgets_dict = dict
    template_render_hook = object

    def __init__(self):
        self.available_widgets_dict = {}
        self.template_render_hook = self.template_render

    def on_socket_connect(self, steamid):
        if isinstance(self.available_widgets_dict, dict) and len(self.available_widgets_dict) >= 1:
            for name, widget in self.available_widgets_dict.items():
                if widget["main_widget"] is not None:
                    widget["main_widget"](self, dispatchers_steamid=steamid)

    def on_socket_disconnect(self, steamid):
        if isinstance(self.available_widgets_dict, dict) and len(self.available_widgets_dict) >= 1:
            for name, widget in self.available_widgets_dict.items():
                if widget["main_widget"] is not None:
                    widget["main_widget"](self, dispatchers_steamid=steamid)

    def on_socket_event(self, event_data, dispatchers_steamid):
        pass

    @staticmethod
    def template_render(*args, **kwargs):
        try:
            template = kwargs.get("template", None)
            rendered_template = template.render(**kwargs)
        except AttributeError as error:
            rendered_template = ""

        return rendered_template

    @staticmethod
    def get_all_available_widgets_dict():
        all_available_widgets_dict = {}
        for loaded_module_identifier, loaded_module in loaded_modules_dict.items():
            if len(loaded_module.available_widgets_dict) >= 1:
                all_available_widgets_dict[loaded_module_identifier] = loaded_module.available_widgets_dict

        return all_available_widgets_dict

    def start(self):
        if isinstance(self.available_widgets_dict, dict) and len(self.available_widgets_dict) >= 1:
            for name, widget in self.available_widgets_dict.items():
                for trigger, handler in widget["handlers"].items():
                    self.dom.data.register_callback(self, trigger, handler)

    def register_widget(self, identifier, widget_dict):
        if widget_dict.get("enabled", True):
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

    def get_current_view(self, dispatchers_steamid):
        return (
            self.dom.data
            .get(self.get_module_identifier(), {})
            .get("visibility", {})
            .get(dispatchers_steamid, {})
            .get("current_view", "frontend")
        )

    def set_current_view(self, dispatchers_steamid, options):
        self.dom.data.upsert({
            self.get_module_identifier(): {
                "visibility": {
                    dispatchers_steamid: options
                }
            }
        }, dispatchers_steamid=dispatchers_steamid)
