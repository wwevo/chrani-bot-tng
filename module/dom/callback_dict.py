from collections import Mapping


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kw):
        self.registered_callbacks = {}
        super().__init__(*args, **kw)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def update(self, *args, **kw):
        super().update(*args, **kw)

    def upsert(self, updated_values_dict, dict_to_update=None):
        if dict_to_update is None:
            dict_to_update = self

        for k, v in updated_values_dict.items():
            if len(self.registered_callbacks) >= 1 and k in self.registered_callbacks.keys():
                updated_values_dict = self.registered_callbacks[k](updated_values_dict, dict_to_update)
            d_v = dict_to_update.get(k)
            if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                self.upsert(v, d_v)
            else:
                dict_to_update[k] = v  # or d[k] = v if you know what you're doing

    def register_callback(self, dict_to_monitor, callback):
        self.registered_callbacks[dict_to_monitor] = callback

