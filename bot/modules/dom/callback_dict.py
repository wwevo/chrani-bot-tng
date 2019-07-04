from collections import Mapping, deque
from threading import Thread
from copy import deepcopy
import re


class CallbackDict(dict, object):

    registered_callbacks = dict

    def __init__(self, *args, **kw):
        self.registered_callbacks = {}
        super().__init__(*args, **kw)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def upsert(self, *args, **kwargs):
        def get_callback_package(updated_values, old_values, dispatchers_steamid, callback):
            callback_kwargs = {
                "updated_values_dict": deepcopy(updated_values),
                "old_values_dict": deepcopy(old_values),
                "dispatchers_steamid": dispatchers_steamid
            }

            return {
                "target": callback["callback"],
                "args": [callback["module"]],
                "kwargs": callback_kwargs
            }

        def construct_full_path(current_path, new_key, current_layer):
            any_steamid = re.search(r"(?P<steamid>\d{17})", new_key, re.MULTILINE)
            if any_steamid:
                """ substitute any steam id with a placeholder for matching """
                try:
                    current_path[current_layer] = "%steamid%"
                except IndexError:
                    current_path.append("%steamid%")
            else:
                try:
                    current_path[current_layer] = new_key
                except IndexError:
                    current_path.append(new_key)

            return "/".join(current_path)

        updated_values_dict = args[0]
        dict_to_update = kwargs.get("dict_to_update", self)
        overwrite = kwargs.get("overwrite", False)
        path = kwargs.get("path", [])
        dispatchers_steamid = kwargs.get("dispatchers_steamid", None)
        layer = kwargs.get("layer", 0)
        callbacks = kwargs.get("callbacks", None)
        mode = kwargs.get("mode", "upsert")
        maxlen = kwargs.get("maxlen", None)

        if layer == 0 and callbacks is None:
            callbacks = []

        path = path[0:layer]

        """" recursion happens in this section """
        for k, v in updated_values_dict.items():
            full_path = construct_full_path(path, k, layer)

            if mode == "append":
                if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                    for callback in self.registered_callbacks[full_path]:
                        callbacks.append(get_callback_package(updated_values_dict, dict_to_update, dispatchers_steamid, callback))

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
                    self.upsert(v, dict_to_update=d_v, path=path, maxlen=maxlen, layer=layer+1, callbacks=callbacks, mode=mode)

            elif mode == "upsert":
                forced_overwrite = False
                if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                    if overwrite is True:
                        forced_overwrite = True
                        dict_to_update[k] = v

                    try:
                        for callback in self.registered_callbacks[full_path]:
                            if isinstance(updated_values_dict[k], Mapping) and len(updated_values_dict[k]) < 1:
                                # print("##### EMPTY?? {}:{}".format(updated_values_dict[k], dict_to_update[k]))
                                continue

                            callbacks.append(get_callback_package(updated_values_dict, dict_to_update, dispatchers_steamid, callback))

                    except KeyError:
                        # not present in the target dict, skipping
                        pass

                d_v = dict_to_update.get(k)
                if not forced_overwrite:
                    if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                        self.upsert(v, dict_to_update=d_v, overwrite=overwrite, path=path, dispatchers_steamid=dispatchers_steamid, layer=layer+1, callbacks=callbacks)
                    elif isinstance(v, Mapping) and len(v) >= 1:
                        dict_to_update[k] = v
                        combined_full_path = "{}/{}".format(full_path, next(iter(v)))
                        try:
                            for callback in self.registered_callbacks[combined_full_path]:
                                callbacks.append(get_callback_package(updated_values_dict, dict_to_update, dispatchers_steamid,callback))

                        except KeyError:
                            # not present in the target dict, skipping
                            pass

                    else:
                        dict_to_update[k] = v

        if layer != 0:
            return
        
        """ we've reached the end of all recursions """
        for callback in callbacks:
            Thread(
                target=callback["target"],
                args=callback["args"],
                kwargs=callback["kwargs"]
            ).start()

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
