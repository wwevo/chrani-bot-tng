from threading import Thread
from bot.mixins.callback_handler import CallbackHandler


class WidgetRenderer(CallbackHandler):
    """
    Extends CallbackHandler with widget-specific functionality.

    Adds:
    - Template rendering
    - View management (for multi-view widgets)
    - Socket connect handler for initial widget rendering
    """
    available_widgets_dict = dict
    template_render_hook = object

    def __init__(self):
        super().__init__()
        self.available_widgets_dict = {}
        self.template_render_hook = self.template_render

    def on_socket_connect(self, steamid):
        """
        Called when a client connects via WebSocket.
        Triggers initial rendering for all enabled widgets.
        """
        if isinstance(self.available_widgets_dict, dict) and len(self.available_widgets_dict) >= 1:
            print("starting widgets {} for {}".format(
                self.get_module_identifier(),
                list(self.available_widgets_dict.keys())
            ))
            for name, widget_meta in self.available_widgets_dict.items():
                if widget_meta.get("main_widget") is not None:
                    # Build callback_meta for widget
                    callback_meta = {
                        "type": "widget",
                        "widget": widget_meta,
                        "event": "socket_connect"
                    }

                    Thread(
                        target=widget_meta["main_widget"],
                        args=(self, callback_meta, steamid)
                    ).start()

    @staticmethod
    def template_render(*args, **kwargs):
        """Helper method for rendering Jinja2 templates"""
        try:
            template = kwargs.get("template", None)
            rendered_template = template.render(**kwargs)
        except AttributeError:
            rendered_template = ""
        return rendered_template

    @staticmethod
    def get_all_available_widgets_dict():
        """Get all registered widgets from all loaded modules"""
        from bot import loaded_modules_dict
        all_widgets = {}
        for module_id, module in loaded_modules_dict.items():
            if hasattr(module, 'available_widgets_dict') and len(module.available_widgets_dict) >= 1:
                all_widgets[module_id] = module.available_widgets_dict
        return all_widgets

    def register_widget(self, identifier, widget_dict):
        """
        Register a widget. Widgets are special callback handlers with rendering capability.
        Also registers as callback_handler for data-driven updates.
        """
        self.available_widgets_dict[identifier] = widget_dict
        # Also register as callback handler
        self.register_callback_handler(identifier, widget_dict)

    def get_current_view(self, widget_name, dispatchers_steamid):
        """
        Get the current view for a multi-view widget.
        Returns the view name (e.g., "main_view", "options_view").
        """
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
        """
        Set the current view for a widget.
        Used for multi-view widgets to track which view each user is seeing.
        """
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
