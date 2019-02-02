from collections import Mapping
from threading import Thread


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kw):
        self.registered_callbacks = {}
        super().__init__(*args, **kw)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def append(self, updated_values_dict, dict_to_update=None, path=None):
        if dict_to_update is None:
            dict_to_update = self
        if path is None:
            path = []

        for k, v in updated_values_dict.items():
            path.append(k)
            full_path = "/".join(path)
            if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                for callback in self.registered_callbacks[full_path]:
                    Thread(
                        target=callback["callback"],
                        args=(callback["module"], CallbackDict(updated_values_dict), dict_to_update)
                    ).start()

                try:
                    dict_to_update[k].append(v)
                except KeyError:
                    dict_to_update[k] = [v]
                except AttributeError:
                    pass

                return

            d_v = dict_to_update.get(k)
            if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                self.append(v, d_v, path=path)

    def update_value(self, dict_to_update, key, value):
        # TODO: only update changed values?
        dict_to_update[key] = value

    def upsert(self, updated_values_dict, dict_to_update=None, overwrite=False, path=None):
        if dict_to_update is None:
            dict_to_update = self
        if path is None:
            path = []

        for k, v in updated_values_dict.items():
            path.append(k)
            full_path = "/".join(path)
            forced_overwrite = False
            if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                for callback in self.registered_callbacks[full_path]:
                    Thread(
                        target=callback["callback"],
                        args=(callback["module"], CallbackDict(updated_values_dict), dict_to_update)
                    ).start()

                if overwrite is True:
                    forced_overwrite = True
                    self.update_value(dict_to_update, k, v)

            d_v = dict_to_update.get(k)
            if not forced_overwrite:
                if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                    self.upsert(v, d_v, overwrite=overwrite, path=path)
                else:
                    self.update_value(dict_to_update, k, v)

    def register_callback(self, module, dict_to_monitor, callback):
        try:
            self.registered_callbacks[dict_to_monitor].append({
                "callback": callback,
                "module": module
            })
        except KeyError as error:
            self.registered_callbacks[dict_to_monitor] = [{
                "callback": callback,
                "module": module
            }]
