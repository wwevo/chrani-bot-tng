from importlib import import_module
from os import path, listdir, pardir

from bot import loaded_modules_dict


class Widget(object):
    available_widgets_dict = dict
    template_render_hook = object

    def __init__(self):
        self.available_widgets_dict = {}
        self.template_render_hook = self.template_render

    def on_socket_connect(self, steamid):
        """ widgets need to know that they are now online!"""
        if isinstance(self.available_widgets_dict, dict) and len(self.available_widgets_dict) >= 1:
            print("starting widgets {} for {}".format(self.get_module_identifier(), list(self.available_widgets_dict.keys())))
            for name, widget_meta in self.available_widgets_dict.items():
                if widget_meta["main_widget"] is not None:
                    self.spawn_tracked(
                        f"widget_{name}",
                        widget_meta["main_widget"],
                        self, widget_meta,
                        dispatchers_id=steamid,
                        timeout=30  # Widgets should complete within 30 seconds
                    )

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
                for trigger, handler in widget.get("handlers").items():
                    if widget.get("enabled", True):
                        self.dom.data.register_callback(self, trigger, handler)

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

    def get_current_view(self, widget_name, dispatchers_steamid):
        active_dataset = self.dom.data.get("module_game_environment", {}).get("active_dataset")
        current_view = (
            self.dom.data
            .get(self.get_module_identifier(), {})
            .get(active_dataset, {})
            .get("visibility", {})
            .get(dispatchers_steamid, {})
            .get("{}_view".format(widget_name))
        )
        if current_view is None:
            self.set_current_view(dispatchers_steamid, {
                '{}_view'.format(widget_name): "main_view"
            })
            return "main_view"

        return current_view

    def set_current_view(self, dispatchers_steamid, options):
        active_dataset = self.dom.data.get("module_game_environment", {}).get("active_dataset")
        self.dom.data.upsert({
            self.get_module_identifier(): {
                active_dataset: {
                    "visibility": {
                        dispatchers_steamid: options
                    }
                }
            }
        }, dispatchers_steamid=dispatchers_steamid)
