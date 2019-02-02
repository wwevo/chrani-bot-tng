from collections import Mapping
from threading import Thread


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kw):
        self.registered_callbacks = {}
        super().__init__(*args, **kw)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def append(self, updated_values_dict, dict_to_update=None):
        if dict_to_update is None:
            dict_to_update = self

        for k, v in updated_values_dict.items():
            if len(self.registered_callbacks) >= 1 and k in self.registered_callbacks.keys():
                Thread(
                    target=self.registered_callbacks[k]["callback"],
                    args=(
                        self.registered_callbacks[k]["module"], CallbackDict(updated_values_dict), dict_to_update
                    )
                ).start()

                try:
                    dict_to_update[k].append(v)
                except KeyError:
                    dict_to_update[k] = []
                    dict_to_update[k].append(v)
                except AttributeError:
                    pass

                return

            d_v = dict_to_update.get(k)
            if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                self.append(v, d_v)

    def upsert(self, updated_values_dict, dict_to_update=None, overwrite=False):
        if dict_to_update is None:
            dict_to_update = self

        for k, v in updated_values_dict.items():
            if len(self.registered_callbacks) >= 1 and k in self.registered_callbacks.keys():
                # we will only call the callback if stuff has actually changed ^^
                Thread(
                    target=self.registered_callbacks[k]["callback"],
                    args=(
                        self.registered_callbacks[k]["module"], CallbackDict(updated_values_dict), dict_to_update
                    )
                ).start()
                if overwrite is True:
                    dict_to_update[k] = v
                    return

            d_v = dict_to_update.get(k)
            if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                self.upsert(v, d_v, overwrite=overwrite)
            else:
                dict_to_update[k] = v  # or d[k] = v if you know what you're doing

    def register_callback(self, module, dict_to_monitor, callback):
        self.registered_callbacks[dict_to_monitor] = {
            "callback": callback,
            "module": module
        }


