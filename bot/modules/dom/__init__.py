import json

from bot import loaded_modules_dict
from bot.module import Module
from .callback_dict import CallbackDict

class Dom(Module):
    data = CallbackDict

    def __init__(self):
        setattr(self, "default_options", {
            "module_name": self.get_module_identifier()[7:],
            "run_observer_interval": 5
        })

        setattr(self, "required_modules", [])

        self.data = CallbackDict()
        self.next_cycle = 0

        Module.__init__(self)

    @staticmethod
    def get_module_identifier():
        return "module_dom"

    def setup(self, options=None):
        Module.setup(self, options)
        self.run_observer_interval = self.options.get(
            "run_observer_interval", self.default_options.get("run_observer_interval", None)
        )

    def get_updated_or_default_value(self, module_identifier, identifier, updated_values_dict, default_value):
        try:
            updated_or_default_value = updated_values_dict.get(
                identifier, self.data.get(module_identifier).get(identifier, default_value)
            )
        except AttributeError as error:
            updated_or_default_value = default_value

        return updated_or_default_value

    def get_dom_element_by_query(
            self,
            dictionary=None,
            target_module="module_dom",
            query="",
            current_layer=0,
            path=None
    ):
        active_dataset = self.data.get("module_game_environment", {}).get("active_dataset", None)
        starting_layer = len(loaded_modules_dict[target_module].dom_element_root)
        if path is None:
            path = []
        if dictionary is None:
            dictionary = self.data.get(target_module, {}).get(active_dataset, {}).get("elements", {})

        for key, value in dictionary.items():
            if type(value) is dict:
                yield from self.get_dom_element_by_query(
                    dictionary=value,
                    target_module=target_module,
                    query=query,
                    current_layer=current_layer + 1,
                    path=path + [key]
                )
            else:
                if current_layer >= starting_layer and key == query:
                    yield path, key, value

    @staticmethod
    def pretty_print_dict(dict_to_print=dict):
        print(json.dumps(dict_to_print, sort_keys=True, indent=4))

    # run() is inherited from Module - periodic actions loop runs automatically!

loaded_modules_dict[Dom().get_module_identifier()] = Dom()
