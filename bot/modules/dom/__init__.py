from bot.module import Module
from bot import loaded_modules_dict
from .callback_dict import CallbackDict


class Dom(Module):
    data = CallbackDict

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })

        setattr(self, "required_modules", [])

        self.data = CallbackDict()
        self.run_observer_interval = 5
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_dom"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion


loaded_modules_dict[Dom().get_module_identifier()] = Dom()
