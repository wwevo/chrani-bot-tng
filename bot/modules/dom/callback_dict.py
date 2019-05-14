from collections import Mapping,deque
from threading import Thread
import re


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kw):
        self.registered_callbacks = {}
        super().__init__(*args, **kw)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def append(self, updated_values_dict, dict_to_update=None, path=None, maxlen=None, dispatchers_steamid=None):
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
                        args=[callback["module"]],
                        kwargs={
                            "updated_values_dict": CallbackDict(updated_values_dict),
                            "old_values_dict": dict_to_update,
                            "dispatchers_steamid": dispatchers_steamid
                        }
                    ).start()

                try:
                    dict_to_update[k].append(v)
                except KeyError:
                    if maxlen is not None:
                        dict_to_update[k] = deque(maxlen=maxlen)
                    else:
                        dict_to_update[k] = []

                    dict_to_update[k].append(v)
                except AttributeError:
                    pass

                return

            d_v = dict_to_update.get(k)
            if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                self.append(v, d_v, path=path, maxlen=maxlen)

    def upsert(self, updated_values_dict, dict_to_update=None, overwrite=False, path=None, dispatchers_steamid=None):
        if dict_to_update is None:
            dict_to_update = self
        if path is None:
            path = []

        for k, v in updated_values_dict.items():
            path.append(k)
            full_path = "/".join(path)

            regex = r"\d{17}"
            for match in re.finditer(regex, k, re.MULTILINE):
                path[-1] = "%steamid%"
                full_path = "/".join(path)

            forced_overwrite = False
            if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                if overwrite is True:
                    forced_overwrite = True
                    dict_to_update[k] = v

                try:
                    for callback in self.registered_callbacks[full_path]:
                        Thread(
                            target=callback["callback"],
                            args=[callback["module"]],
                            kwargs={
                                "updated_values_dict": CallbackDict(updated_values_dict),
                                "old_values_dict": dict_to_update,
                                "dispatchers_steamid": dispatchers_steamid
                            }
                        ).start()
                except KeyError:
                    # not present in the target dict, skipping
                    pass

            d_v = dict_to_update.get(k)
            if not forced_overwrite:
                if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                    self.upsert(v, d_v, overwrite=overwrite, path=path, dispatchers_steamid=dispatchers_steamid)
                elif isinstance(v, Mapping) and len(v) >= 1:
                    dict_to_update[k] = v
                    combined_full_path = "{}/{}".format(full_path, next(iter(v)))
                    try:
                        for callback in self.registered_callbacks[combined_full_path]:
                            Thread(
                                target=callback["callback"],
                                args=[callback["module"]],
                                kwargs={
                                    "updated_values_dict": CallbackDict(v),
                                    "old_values_dict": dict_to_update[k],
                                    "dispatchers_steamid": dispatchers_steamid
                                }
                            ).start()
                    except KeyError:
                        # not present in the target dict, skipping
                        pass

                else:
                    dict_to_update[k] = v

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
