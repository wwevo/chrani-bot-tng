import json
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

    def get_updated_or_default_value(self, module_identifier, identifier, updated_values_dict, default_value):
        try:
            updated_or_default_value = updated_values_dict.get(
                identifier, self.data.get(module_identifier).get(identifier, default_value)
            )
        except AttributeError as error:
            updated_or_default_value = default_value

        return updated_or_default_value

    """ method to retrieve any dom elements based on their name or key """
    def get_dom_element_by_query(
            self,
            dictionary=None,
            target_module="module_dom",
            query="",
            current_layer=0,
            path=None
    ):
        starting_layer = len(loaded_modules_dict[target_module].dom_element_root)
        if path is None:
            path = []
        if dictionary is None:
            dictionary = self.data.get(target_module, {}).get("elements", {})

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
                    yield (path, key, value)

    @staticmethod
    def pretty_print_dict(dict_to_print=dict):
        print(json.dumps(dict_to_print, sort_keys=True, indent=4))


loaded_modules_dict[Dom().get_module_identifier()] = Dom()
