from importlib import import_module
from os import path, listdir, pardir


class CallbackHandler(object):
    """
    Base class for handling callback_dict based reactions.

    Callbacks are registered with callback_dict and triggered when data changes.
    All handlers follow the signature: handler(module, callback_meta, dispatchers_id=None)

    callback_meta contains:
    - method: "upsert", "delete", or "append"
    - matched_path: the callback path that matched
    - original_data: data before change
    - updated_data: data after change
    - dispatchers_id: who triggered the change (optional)
    """
    available_callback_handlers_dict = dict

    def __init__(self):
        self.available_callback_handlers_dict = {}

    def start(self):
        """Register all callback handlers with callback_dict when module starts"""
        try:
            for name, handler_meta in self.available_callback_handlers_dict.items():
                try:
                    for trigger_path, handler_func in handler_meta["handlers"].items():
                        if handler_meta.get("enabled", True):
                            self.dom.data.register_callback(self, trigger_path, handler_func)
                except KeyError:
                    pass
        except (KeyError, AttributeError):
            pass

    def register_callback_handler(self, identifier, handler_dict):
        """Register a callback handler with this module"""
        self.available_callback_handlers_dict[identifier] = handler_dict

    def import_callback_handlers(self):
        """
        Import callback handlers from module directories.
        Looks in both callback_handlers/ and widgets/ directories.
        """
        modules_root_dir = path.join(path.dirname(path.abspath(__file__)), pardir, "modules")
        module_root_dir = path.join(modules_root_dir, self.options['module_name'])

        # Import from callback_handlers directory
        try:
            callback_handlers_dir = path.join(module_root_dir, "callback_handlers")
            for handler_file in listdir(callback_handlers_dir):
                if handler_file in ('common.py', '__init__.py') or not handler_file.endswith('.py'):
                    continue
                import_module("bot.modules." + self.options['module_name'] + ".callback_handlers." + handler_file[:-3])
        except (FileNotFoundError, ModuleNotFoundError):
            pass

        # Import from widgets directory (widgets are also callback handlers)
        try:
            widgets_dir = path.join(module_root_dir, "widgets")
            for widget_file in listdir(widgets_dir):
                if widget_file in ('common.py', '__init__.py') or not widget_file.endswith('.py'):
                    continue
                import_module("bot.modules." + self.options['module_name'] + ".widgets." + widget_file[:-3])
        except (FileNotFoundError, ModuleNotFoundError):
            pass

    @staticmethod
    def get_all_available_callback_handlers_dict():
        """Get all registered callback handlers from all loaded modules"""
        from bot import loaded_modules_dict
        all_handlers = {}
        for module_id, module in loaded_modules_dict.items():
            if hasattr(module, 'available_callback_handlers_dict') and len(module.available_callback_handlers_dict) >= 1:
                all_handlers[module_id] = module.available_callback_handlers_dict
        return all_handlers
