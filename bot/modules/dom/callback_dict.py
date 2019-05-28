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

    def append(self, updated_values_dict, dict_to_update=None, path=None, maxlen=None, dispatchers_steamid=None, layer=0, callbacks=None):
        if layer == 0:
            if callbacks is None:
                callbacks = []

        layer += 1
        if dict_to_update is None:
            dict_to_update = self
        if path is None:
            path = []
        else:
            path = path[0:layer-1]

        for k, v in updated_values_dict.items():
            if re.match(r"\d{17}", k, re.MULTILINE):
                try:
                    path[layer-1] = "%steamid%"
                except IndexError:
                    path.append("%steamid%")
            else:
                try:
                    path[layer-1] = k
                except IndexError:
                    path.append(k)

            full_path = "/".join(path)
            if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                for callback in self.registered_callbacks[full_path]:
                    callbacks.append(Thread(
                        target=callback["callback"],
                        args=[callback["module"]],
                        kwargs={
                            "updated_values_dict": CallbackDict(updated_values_dict),
                            "old_values_dict": dict_to_update,
                            "dispatchers_steamid": dispatchers_steamid
                        }
                    ))

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
                self.append(v, d_v, path=path, maxlen=maxlen, layer=layer, callbacks=callbacks)

        layer -= 1
        if layer == 0:
            for callback in callbacks:
                callback.start()

    def upsert(self, updated_values_dict, dict_to_update=None, overwrite=False, path=None, dispatchers_steamid=None, layer=0, callbacks=None):
        if layer == 0:
            if callbacks is None:
                callbacks = []

        layer += 1
        if dict_to_update is None:
            dict_to_update = self
        if path is None:
            path = []
        else:
            path = path[0:layer-1]

        for k, v in updated_values_dict.items():
            if re.match(r"\d{17}", k, re.MULTILINE):
                try:
                    path[layer-1] = "%steamid%"
                except IndexError:
                    path.append("%steamid%")
            else:
                try:
                    path[layer-1] = k
                except IndexError:
                    path.append(k)

            full_path = "/".join(path)
            forced_overwrite = False
            if len(self.registered_callbacks) >= 1 and full_path in self.registered_callbacks.keys():
                if overwrite is True:
                    forced_overwrite = True
                    dict_to_update[k] = v

                try:
                    for callback in self.registered_callbacks[full_path]:
                        print("{}:{}".format(updated_values_dict[k], dict_to_update[k]))
                        callbacks.append(
                            Thread(
                                target=callback["callback"],
                                args=[callback["module"]],
                                kwargs={
                                    "updated_values_dict": CallbackDict(updated_values_dict),
                                    "old_values_dict": dict_to_update,
                                    "dispatchers_steamid": dispatchers_steamid
                                }
                            )
                        )

                except KeyError:
                    # not present in the target dict, skipping
                    pass

            d_v = dict_to_update.get(k)
            if not forced_overwrite:
                if isinstance(v, Mapping) and isinstance(d_v, Mapping):
                    self.upsert(v, d_v, overwrite=overwrite, path=path, dispatchers_steamid=dispatchers_steamid, layer=layer, callbacks=callbacks)
                elif isinstance(v, Mapping) and len(v) >= 1:
                    dict_to_update[k] = v
                    combined_full_path = "{}/{}".format(full_path, next(iter(v)))
                    try:
                        for callback in self.registered_callbacks[combined_full_path]:
                            callbacks.append(
                                Thread(
                                    target=callback["callback"],
                                    args=[callback["module"]],
                                    kwargs={
                                        "updated_values_dict": CallbackDict(v),
                                        "old_values_dict": dict_to_update[k],
                                        "dispatchers_steamid": dispatchers_steamid
                                    }
                                )
                            )

                    except KeyError:
                        # not present in the target dict, skipping
                        pass

                else:
                    dict_to_update[k] = v
        layer -= 1
        if layer == 0:
            for callback in callbacks:
                callback.start()

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
