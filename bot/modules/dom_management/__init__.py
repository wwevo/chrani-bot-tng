from bot.module import Module
from bot import loaded_modules_dict


class DomManagement(Module):

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:]
        })

        setattr(self, "required_modules", [
            "module_dom",
            "module_webserver"
        ])

        self.run_observer_interval = 5
        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_dom_management"

    # region Standard module stuff
    def setup(self, options=dict):
        Module.setup(self, options)
    # endregion


loaded_modules_dict[DomManagement().get_module_identifier()] = DomManagement()
